import re
import requests
from datetime import datetime
from io import StringIO
from collections.abc import Iterable
from typing import Any

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from .definitions import Definitions
from .utils import configure_logging


logger = configure_logging(streaming=True)


class YfScrapper():
    '''
    Scrapper object to get ticker stats from Yahoo Finance
    '''
    def __init__(self):
        self.headers = Definitions.REQUEST_HEADER
        self.mapping_dict = Definitions.TICKER_METRICS_MAPPING
        self.tickers = {}
        self.compiled_dataframes = None

    def __getattr__(self, ticker: str) -> Any:
        if ticker.isupper() and len(ticker) <= 4: 
            return self.tickers[ticker].T
        else:
            raise KeyError('No such attribute, to get Ticker data, input ticker in caps')

    def __getitem__(self, ticker: str) -> Any:
        if ticker.isupper() and len(ticker) <= 4: 
            return self.tickers[ticker].T
        else:
            raise KeyError('No such attribute, to get Ticker data, input ticker in caps')

    def add_tickers(self, tickers):
        if isinstance(tickers, str):
            self.tickers.setdefault(tickers)
        elif isinstance(tickers, Iterable):
            count = 0
            for ticker in tickers:
                self.tickers.setdefault(ticker)
                count += 1
            logger.info(f'Added {count} tickers')
        else:
            raise TypeError('tickers must be str or iterable list of strings')
    
    def _mapper(self, row):
        '''Helper function to map or return original values'''
        return self.mapping_dict.get(row, row)

    @staticmethod
    def _get_soup(
        ticker: str,
        headers: dict
    ) -> Iterable[pd.DataFrame]:
        url = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup

    @staticmethod
    def _get_dataframes_from_soup(soup):
        df_list = pd.read_html(StringIO(soup.prettify()))

        for idx in range(len(df_list)):
            if len(df_list[idx].columns) > 2:
                df_list[idx] = df_list[idx].iloc[:, :2]
                df_list[idx].columns = [0, 1]
        return df_list

    def get_ticker_stats(self, tickers, clean_df=True):  
        '''
        Function take takes in a list of tickers and scraps the yahoo stats into a dictionary.
        Parameters:
            tickers (str or iterable list of strings): 
                If 'all', will scrap for all the stored tickers, otherwise provide a list of tickers to scrap or a ticker
            clean_df (bool):
                option whether to clean the data
        '''
        if isinstance(tickers, str):
            if tickers.upper() == 'ALL':
                tickers = self.tickers
            elif tickers.upper().startswith('S&P'):
                tickers = self.get_SP500_data(tickers_only=True)
            else:
                tickers = list(tickers)
        elif isinstance(tickers, Iterable):
            pass
        else:
            raise TypeError('tickers must be str or iterable list of strings')

        for ticker in tickers:
            soup = self._get_soup(
                ticker=ticker,
                headers=self.headers
            )
            ticker_name = soup.find("h1").text
            df_list = self._get_dataframes_from_soup(soup)
            df = pd.concat(df_list)
            df.columns = ['metrics', ticker]

            # Header cleaning
            df['metrics'].replace(regex={r'[0-9]$': ''}, inplace=True)  # Removes the annotations appearing at the end of rows
            df['metrics'].replace(regex={r'(\(.+,.+\))': ''}, inplace=True)  # This will specifically remove dates inside brackets, by checking for ','
            df['metrics'] = df['metrics'].str.strip()
            df['metrics'] = df['metrics'].apply(self._mapper)
            df = df.T
            df.columns = df.iloc[0, :]  # Update the first row as the header
            df.insert(0, 'Name', ticker_name)
            df = df.drop('metrics')

            # There are two columns named 'shares short', the latter is for prior month
            idx = df.columns.to_list().index('Shares Short (M) (prior month)')
            updated_columns = df.columns.to_list()
            updated_columns[idx] = 'Shares Short (M)'

            df.columns = updated_columns
            if clean_df:
                df = self.clean_df(df)
            logger.info(f'{df.iloc[0, 0]} : {df.iloc[0, 1]}')
            # Save to the object variable
            self.tickers[ticker] = df

    def clean_df(self, df):
        '''
        Function to cast and clean the dataframe via the following:
        1. Format strings into numbers according (large number format)
        2. Clean stocksplit ratios 
        3. Recast dates into datetime format

        Parameters:
            df (pd.DataFrame) - dataframe for cleaning
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
    
    def compile_dataframes(self):
        '''
        Function to concatenate all the ticker dataframe together
        '''
        dfs = [ticker for ticker in self.tickers.values() if isinstance(ticker, pd.DataFrame)]
        df = pd.concat([*dfs])
        self.compiled_dataframes = df
        return df
        
    def get_SP500_data(self, tickers_only: bool=False, url: str='https://www.slickcharts.com/sp500', tableclass: str ="table-responsive"):
        '''
        Function to scrap the latest S&P data from a website containing S&P data
        Inputs:
            tickers_only: boolean - whether to return the ticker symbols only, or the whole dataframe
            url: string - website url
            tableclass: string - tableclass containing the data
        Returns:
            pd.DataFrame or list
        '''
        resp = requests.get(url, headers = self.headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find(class_ = tableclass)

        table_head = table.find('thead')
        header_list = [th.text.strip() for th in table_head.find_all('th')]

        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        sp_data = []
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            sp_data.append([ele for ele in cols if ele]) # Get rid of empty values

        sp_df = pd.DataFrame(np.array(sp_data))
        sp_df.columns = header_list
        sp_df = sp_df.drop('#', axis=1)
        sp_df['Symbol'].replace(regex={r'[\.]': '-'}, inplace=True) #tickers need to have - instead of . for proper search on yahoo
        logger.info(f'Number of S&P constituent data obtained: {len(sp_df)}')
        if tickers_only:
            return sp_df['Symbol'].to_list()
        else:
            return sp_df

    def to_csv(self, filepath):
        if self.compiled_dataframes:
            self.compiled_dataframes.to_csv(filepath + '.csv')
            logger.info(f'File {filepath} saved!')
