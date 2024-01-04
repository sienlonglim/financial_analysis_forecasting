import re
import requests
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO

class YfScrapper():    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
            }
        self.mapping_dict = {
            'Market Cap (intraday)' : 'Market Cap (B)',
            'Enterprise Value' : 'Enterprise Value (B)',
            '52-Week Change' : '52 Week Change (%)',
            'S&P500 52-Week Change': 'S&P500 52-Week Change (%)',
            'Avg Vol 3 month' : 'Avg Vol 3 month (B)',
            'Avg Vol (10 day)' : 'Avg Vol 10 day (B)',
            'Shares Short' : 'Shares Short (M) (prior month)',
            'Forward Annual Dividend Yield': 'Forward Annual Dividend Yield (%)',
            'Trailing Annual Dividend Yield' : 'Trailing Annual Dividend Yield (%)',
            'Payout Ratio' : 'Payout Ratio (%)',
            'Last Split Factor' : 'Last Split Factor (x:1)',
            'Profit Margin' : 'Profit Margin (%)',
            'Operating Margin (ttm)' : 'Operating Margin (ttm) (%)',
            'Return on Assets (ttm)' : 'Return on Assets (ttm) (%)',
            'Return on Equity (ttm)' : 'Return on Equity (ttm) (%)',
            'Revenue (ttm)' : 'Revenue (ttm) (B)',
            'Quarterly Revenue Growth (yoy)' : 'Quarterly Revenue Growth (yoy) (%)',
            'Gross Profit (ttm)' : 'Gross Profit (ttm) (B)',
            'EBITDA' : 'EBITDA (B)',
            'Net Income Avi to Common (ttm)' : 'Net Income Avi to Common (ttm) (B)',
            'Quarterly Earnings Growth (yoy)' : 'Quarterly Earnings Growth (yoy) (%)',
            'Total Cash (mrq)' :'Total Cash (mrq) (B)',
            'Total Debt (mrq)' :'Total Debt (mrq) (B)',
            'Operating Cash Flow (ttm)' : 'Operating Cash Flow (ttm) (B)',
            'Levered Free Cash Flow (ttm)' : 'Levered Free Cash Flow (ttm) (B)'
        }
        self.tickers = {}

    def add_tickers(self, tickers):
        '''
        Adds a list of tickers to the class instance
        '''
        count = 0
        for ticker in tickers:
            self.tickers.setdefault(ticker)
            count +=1
        print(f'Added {count} tickers')
    
    def _mapper(self, row):
            '''Helper function to map or return original values'''
            return self.mapping_dict.get(row, row)

    def get_ticker_stats(self, tickers, clean_df=True):  
        '''
        Function take takes in a list of tickers and scraps the yahoo stats into a dictionary.
        Input:
            tickers : if 'all', will scrap for all the stored tickers, otherwise provide a list of tickers to scrap or a ticker
        '''
        if isinstance(tickers, str):
            if tickers == 'all':
                tickers = self.tickers
            else:
                tickers = list(tickers)
        elif isinstance(tickers, list) or isinstance(tickers, tuple):
            pass
        else:
            raise TypeError('tickers must be an iterable object of strings')
        
        for ticker in tickers:
            url = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'
            resp = requests.get(url, headers = self.headers)
            print(f'{ticker} status - {resp.status_code}')
            soup = BeautifulSoup(resp.text, "html.parser")
            name = soup.find("h1").text

            # Read the html using pandas to parse tables directly, then concatenate them
            dfs = pd.read_html(StringIO(resp.text))
            df = pd.concat([*dfs])
            df.columns = ['metrics', ticker]
            # Header cleaning
            df['metrics'].replace(regex={r'[0-9]$': ''}, inplace = True) # Removes the annotations appearing at the end of rows
            df['metrics'].replace(regex={r'(\(.+,.+\))': ''}, inplace = True) # This will specifically remove dates inside brackets, by checking for ','
            ### UNRESOLVED, there are tow columns shares short, the latter is for prior month
            df['metrics'] = df['metrics'].str.strip()
            df['metrics'] = df['metrics'].apply(self._mapper)
            df = df.T
            df.columns = df.iloc[0,:] # Update the first row as the header
            df.insert(0, 'Name', name)
            df = df.drop('metrics') # Drop the first row
            idx = df.columns.to_list().index('Shares Short (M) (prior month)')
            updated_columns = df.columns.to_list()
            updated_columns[idx] = 'Shares Short (M)'
            df.columns = updated_columns
            if clean_df:
                df = self.clean_df(df)

            # Save to the object variable
            self.tickers[ticker] = df

    def clean_df(self, df):
        '''
        Function to cast and clean the dataframe via the following:
        1. Format strings into numbers according (large number format)
        2. Clean stocksplit ratios 
        3. Recast dates into datetime format

        Inputs:
        '''
        for col in df.columns:
            if col in ['Dividend Date', 'Ex-Dividend Date', 'Last Split Date', 'Fiscal Year Ends', 'Most Recent Quarter (mrq)']:
                df[col] = df[col].apply(self._date_conversion)
            elif col == 'Last Split Factor (x:1)':
                df[col] = df[col].apply(self._stocksplits)
            else:
                df[col] = df[col].apply(self._num_reformat)
        return df

    def _num_reformat(self, x):
        '''
        Helper function to reformat large sums to be in Billions and removing % and commas
        Casts numerical values into float type
        '''
        if isinstance(x, str):
            x = re.sub("[,]", "", x)
            if x[-1] == 'T':
                x = round(float(x[:-1])*1000,2)
            elif x[-1] == 'B':
                x = round(float(x[:-1]),2)
            elif x[-1] == 'M':
                x = round(float(x[:-1])*0.001,2)
            elif x[-1] == 'k':
                x = round(float(x[:-1])*0.000001,2)
            elif x[-1] == '%':
                x = round(float(x[:-1]),2)             
            elif x == "N/A":
                x = 0
        return x

    def _stocksplits(self, x):
        '''
        Changes split factors into x:1 whole ratios
        '''
        if isinstance(x, str):
            x = x.split(':')
            return round(int(x[0])/ int(x[1]),2)
        else:
            return x
    
    def _date_conversion(self, x):
        '''
        Parses dates into datetime format at the end of the dataframe
        '''
        if isinstance(x, str):
            # Dec 30, 2022
            return datetime.strptime(x, '%b %d, %Y').date()
        else:
            return x
    
    def combine_data(self):
        dfs = self.tickers.values()
        df = pd.concat([*dfs])
        return df
        

