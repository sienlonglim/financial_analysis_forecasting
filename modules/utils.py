import re
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


#headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def get_SP500_data(tickers_only: bool=False, url: str='https://www.slickcharts.com/sp500', tableclass: str ="table-responsive"):
    '''
    Function to scrap the latest S&P data from a website containing S&P data
    Inputs:
        tickers_only: boolean - whether to return the ticker symbols only, or the whole dataframe
        url: string - website url
        tableclass: string - tableclass containing the data
    Returns:
        pd.DataFrame or list
    '''
    resp = requests.get(url, headers = headers)
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
    print(f'Number of S&P constituent data obtained: {len(sp_df)}')
    if tickers_only:
        return sp_df['Symbol'].to_list()
    else:
        return sp_df

def get_yf_headers(from_webpage: bool, ticker_sample: str = None)-> list: 
    '''
    Retrieves the dataframe headers from the yahoo finance statistics page
    Input:
        from_webpage: bool - whether to scrap from webpage or use hardcoded metrics with added units
        ticker_sample: string - ticker to use for the scrapping
    Returns 
        metrics: list of strings to use as the header for our dataframe
    '''
    if from_webpage:
        url = f'https://finance.yahoo.com/quote/{ticker_sample}/key-statistics?p={ticker_sample}'
        resp = requests.get(url, headers = headers)
        print(f'Using {ticker_sample} for headers, status - {resp.status_code}')
        soup = BeautifulSoup(resp.text, "html.parser")

        titles = ['Ticker']
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            ele = cols[0].text.strip() 
            titles.append(ele)

        metrics_df = pd.DataFrame({"Metrics":titles})
        metrics_df['Metrics'].replace(regex={r'[0-9]$': ''}, inplace = True) #removes the annotations appearing at the end of rows
        metrics_df.iloc[24:29,0].replace(regex={r'(\(.+\))': ''}, inplace = True) #remove the dates under rows 24-28
        metrics = metrics_df['Metrics'].tolist()
        print(f'Extraction of headers complete! Total metric columns = {len(metrics)}')
    else:
        hardcoded_metrics = [
            'Name',
            'Market Cap (B)',
            'Enterprise Value (B)',
            'Trailing P/E',
            'Forward P/E',
            'PEG Ratio (5 yr expected)',
            'Price/Sales (ttm)',
            'Price/Book (mrq)',
            'Enterprise Value/Revenue',
            'Enterprise Value/EBITDA',
            'Beta (5Y Monthly)',
            '52 Week Change (%)',
            'S&P500 52-Week Change (%)',
            '52 Week High',
            '52 Week Low',
            '50-Day Moving Average',
            '200-Day Moving Average',
            'Avg Vol 3 month (M)',
            'Avg Vol 10 day (M)',
            'Shares Outstanding',
            'Implied Shares Outstanding',
            'Float',
            '% Held by Insiders',
            '% Held by Institutions',
            'Shares Short (M)',
            'Short Ratio (M)',
            'Short % of Float',
            'Short % of Shares Outstanding',
            'Shares Short',
            'Forward Annual Dividend Rate',
            'Forward Annual Dividend Yield (%)',
            'Trailing Annual Dividend Rate',
            'Trailing Annual Dividend Yield (%)',
            '5 Year Average Dividend Yield',
            'Payout Ratio (%)',
            'Dividend Date',
            'Ex-Dividend Date',
            'Last Split Factor (x:1)',
            'Last Split Date',
            'Fiscal Year Ends',
            'Most Recent Quarter (mrq)',
            'Profit Margin (%)',
            'Operating Margin (ttm) (%)',
            'Return on Assets (ttm) (%)',
            'Return on Equity (ttm) (%)',
            'Revenue (ttm) (B)',
            'Revenue Per Share (ttm)',
            'Quarterly Revenue Growth (yoy) (%)',
            'Gross Profit (ttm) (B)',
            'EBITDA (B)',
            'Net Income Avi to Common (ttm) (B)',
            'Diluted EPS (ttm)',
            'Quarterly Earnings Growth (yoy) (%)',
            'Total Cash (mrq) (B)',
            'Total Cash Per Share (mrq)',
            'Total Debt (mrq) (B)',
            'Total Debt/Equity (mrq)',
            'Current Ratio (mrq)',
            'Book Value Per Share (mrq)',
            'Operating Cash Flow (ttm) (B)',
            'Levered Free Cash Flow (ttm) (B)']
    return metrics

def scrap_ticker(tickers, data_dict, metrics, sleeptime=2, batch_interval=50):  
    '''
    Function take takes in a list of tickers and scraps the yahoo stats into a dictionary.
    Input:
        tickers : list of tickers
        data_dict : dictionary to update with the scrapped data, should be created outside the function
        metrics : list of headers
        sleeptime : time to sleep between scraps
        batch_interval : number of scraps before a longer rest
    Returns:
        list of tickers with failed scraps
    '''
    
    start_time = datetime.now()
    
    #check if there is any existing data in all_data (dictionary), if yes, assigns this run to the next batch number
    if data_dict:
        batch_number = max(data_dict.keys())+1
        print(f'Batch number: {batch_number}')
    else:
        batch_number = 1
    
    #initialize the batch_count, and wait_counter (for increasing waits between failed scraps)
    batch_count = 0
    wait_counter = 1

    #initialize list for collecting batch data and list for collecting tickers with errors
    batch_data = []
    missed_tickers=[]
    
    try:
        for count, ticker in enumerate(tickers):
            url = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'
            resp = requests.get(url, headers = headers)
            print(f'{ticker} status - {resp.status_code}, {count+1}/{len(tickers)}', end=' ')
            soup = BeautifulSoup(resp.text, "html.parser")
            
            title = soup.find("h1")
            data= [title.text]
            
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                ele = cols[1].text.strip()
                data.append(ele)
            
            #to account for errors in the extraction length or data
            if len(data)!=len(metrics) or data[1] == 'N/A':
                if len(data)!=len(metrics):
                    print(f'length error({len(data)} instead of {len(metrics)}) in {ticker}')
                elif data[1] == 'N/A':
                    print(f'N/A found in Marketcap of {ticker}')
                missed_tickers.append(ticker)
                print(f'Sleeping for {sleeptime*2*wait_counter}s')
                time.sleep(sleeptime*2*wait_counter)
                wait_counter +=1
            else:
                batch_data.append(data)
                print(f'complete!')
                batch_count +=1
                time.sleep(sleeptime)

            #code to sleep after a batch
            if batch_count == batch_interval:
                data_dict[batch_number] = pd.DataFrame(batch_data)
                print(f'\nLength of info extracted is {len(batch_data)} in batch {batch_number} \n')
                batch_count = 0
                batch_number +=1
                batch_data = []
                print(f'Sleeping for {sleeptime*2}s')
                time.sleep(sleeptime*2)
    except Exception as e:
        print(e)
    finally:
        #the final appending for last batch with n smaller than 50
        data_dict[batch_number] = pd.DataFrame(batch_data)
        print(f'Length of info extracted is {len(batch_data)} in batch {batch_number}')
        end_time = datetime.now()
        print('Elapsed time was', (end_time - start_time))
        print()
        return missed_tickers