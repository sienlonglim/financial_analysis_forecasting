from typing import Any
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from modules.utils import logger

class Forecaster():
    '''
    Object class to retrieve prices, forecast, and determine buy/sell actions
    '''
    def __init__(self, *args, **kwargs)-> None:
        '''
        Initialize with any specified tickers
        Parameters:
            tickers (str) : tickers to store
            price_type (str) : type of price during the interval 'Open', 'Close', 'High', 'Low'
            period (str) : length of time series - '5y', '1y', 'ytd', '10y'
            interval (str) : Interval of prices - '1wk', '1d'
            order (tuple) : (p, d, q)
            seasonal_order (tuple) : (P, D, Q, m)
        '''
        self.tickers = {}
        for arg in args:
            if arg.isupper() and len(arg)<=4: 
                self.tickers.setdefault(arg)
            else:
                logger.info(f'Invalid ticker: {arg}, ticker must be in uppercase only')
        
        self.price_type = kwargs.get("price_type", 'Close')
        self.period = kwargs.get("period", '5y')
        self.interval = kwargs.get("interval", '1wk')
        self.order = kwargs.get("order", (0, 1, 1))
        self.seasonal_order = kwargs.get("seasonal_order", (2, 1, 0, 52))

    def __repr__(self) -> str:
        '''
        Shows the main parameters of the class object
        '''
        return (f'Forecaster(price_type={self.price_type}, period={self.period},'
                f'interval={self.interval}, order={self.order}, seasonal_order={self.seasonal_order}, tickers={self.tickers.values()}')

    def __getattr__(self, ticker: str) -> Any:
        '''
        Modified dunder method to call ticker info directly from class object
        Parameters:
            ticker (str) : ticker to get infomation
        Returns:
            dictionary containing the data
            keys -> ('forecast' / 'ts / 'max_profit' / 'max_profit_history' / 'best_trades' / 'best_trades_history')
        '''
        if ticker.isupper() and len(ticker)<=4: 
            return self.tickers[ticker]
        else:
            raise KeyError('No such attribute, to get Ticker data, input ticker in caps')

    def __getitem__(self, ticker: str) -> Any:
        '''
        Modified dunder method to call ticker info directly from class object
        Parameters:
            ticker (str) : ticker to get infomation
        Returns:
            dictionary containing the data
            keys -> ('forecast' / 'ts / 'max_profit' / 'max_profit_history' / 'best_trades' / 'best_trades_history')
        '''
        if ticker.isupper() and len(ticker)<=4: 
            return self.tickers[ticker]
        else:
            raise KeyError('No such attribute, to get Ticker data, input ticker in caps')

    def forecast(self, *args, **kwargs):
        '''
        Forecasts with SARIMA
        Parameters:
            tickers (str) : tickers to forecast, if none are specified, uses all the tickers stored in object
            price_type (str) : type of price during the interval 'Open', 'Close', 'High', 'Low'
            period (str) : length of time series - '5y', '1y', 'ytd', '10y'
            interval (str) : Interval of prices - '1wk', '1d'
            order (tuple) : (p, d, q)
            seasonal_order (tuple) : (P, D, Q, m)
        '''
        price_type = kwargs.get("price_type", self.price_type)
        period = kwargs.get("period", self.period)
        interval = kwargs.get("interval", self.interval)
        order = kwargs.get("order", self.order)
        seasonal_order = kwargs.get("seasonal_order", self.seasonal_order)

        if not args:
            args = self.tickers.keys()

        for ticker in args:
            logger.info(f'Forecasting for {ticker}')
            stock = yf.Ticker(ticker)
            # logger.info(stock.info)

            # get historical market data
            df = stock.history(period=period, interval=interval)
            if interval == '1wk':
                ts = df[[price_type]].to_period('W')
            elif interval == '1d':
                ts = df[[price_type]].to_period('D')

            model = ARIMA(ts, order=order,seasonal_order=seasonal_order)
            model_fit = model.fit()
            forecast = model_fit.predict(start=len(df), end = len(df)+seasonal_order[-1], dynamic=False)     
            self.tickers[ticker] = {'ts': ts, 'forecast': forecast, 'model':model_fit}

    def forecast_validation(self, ticker:str = None, validation_periods:int = 52, plot:bool=True, forecast_period_only = True, **kwargs):
        '''
        Forecasts with SARIMA
        Parameters:
            tickers (str) : ticker to validate
            validation_periods (int) : periods to validate (from latest period)
            plot (bool) : whether to plot out forecast vs validation
            forecast_period_only : plot only the forecast period
            **kwargs (see documentation on forecast())
        '''
        price_type = kwargs.get("price_type", self.price_type)
        period = kwargs.get("period", self.period)
        interval = kwargs.get("interval", self.interval)
        order = kwargs.get("order", self.order)
        seasonal_order = kwargs.get("seasonal_order", self.seasonal_order)

        if not ticker:
            ticker = list(self.tickers.keys())[0]
        logger.info(f'Validating forecast for {ticker}')
        stock = yf.Ticker(ticker)
        # logger.info(stock.info)

        # Get historical market data
        df = stock.history(period=period, interval=interval)
        if interval == '1wk':
            ts = df[[price_type]].to_period('W')
        elif interval == '1d':
            ts = df[[price_type]].to_period('D')
        
        train, test = ts[:-validation_periods], ts[-validation_periods:]
        logger.info(f'Train periods: {len(train)}, Validation periods: {len(test)}')

        # Forecast for the test period
        model = ARIMA(train, order=order,seasonal_order=seasonal_order)
        model_fit = model.fit()
        forecast = model_fit.predict(start=len(train), end = len(train)+len(test), dynamic=False)  

        # Calculate MSE
        mse = 1/len(test)*np.sum((test.squeeze() - (forecast.shift(-1)))**2)
        logger.info(f'MSE: {mse}')
        logger.info(f'AIC: {model_fit.aic}')

        # Plot both yhat and y
        if plot:
            plt.figure(figsize=(14,6))
            plt.title(f'Validation for {ticker}')
            plt.plot(test.to_timestamp(), color='grey', label='Actual')
            plt.plot(forecast.to_timestamp().shift(-1), color='salmon', label='Forecast')
            if not forecast_period_only:
                plt.plot(ts.to_timestamp())
            else:
                plt.xticks(forecast.index, rotation=45, fontsize=8)
                plt.legend()
                plt.grid()
        return mse, model_fit.aic
    
    def plot_forecast(self, ticker: str=None, forecast_only: bool=False):
        '''
        Plots the forecasts and/or timeseries of prices
        Parameters:
            ticker (str) : ticker to plot from stored forecast
            forecast_only (bool) : whether to plot only the forecast or include past_prices
        '''
        try:
            # Use the init ticker
            if not ticker:
                ticker = list(self.tickers.keys())[0]
            ticker_data = self.tickers[ticker]
            ts, forecast = ticker_data['ts'], ticker_data['forecast']

            # Use .to_timestamp() to convert period back into timestamp for plotting
            plt.figure(figsize=(14,6))
            plt.title(f'Forecast for {ticker}')
            plt.plot(forecast.to_timestamp(), color='salmon', label='Forecast')
            if not forecast_only:
                plt.plot(ts.to_timestamp(), color='grey', label='Actual')
            else:
                plt.xticks(forecast.index, rotation=45, fontsize=8)
                plt.grid()
            plt.legend()

        except AttributeError as e:
            logger.info(f'No forecasting done yet for {ticker}')            

    def find_max_profit(self, *args):
        '''
        Finds the maximum profit possible without trading
        Parameters:
            ticker (str) : ticker to plot from stored forecast
        '''
        if not args:
            args = self.tickers.keys()

        for ticker in args:
            try:
                ticker_data = self.tickers.get(ticker, None)     
                forecast = ticker_data.get('forecast', None)  
                max_profit = 0
                high, low = None, None
                last_profit = None
                data = {}
                for period, price in zip(forecast.index, forecast):
                    data[period] = dict(current=price) # Saves every period as index
                    if not low or not high:
                        # Initial assignments
                        low = high = price 
                        low_idx = high_idx = period
                        # For edge case, where new_low is the first item
                        data[period]['new_low'] = price

                    # Find new lows, including the index
                    if price < low:
                        low, low_idx = price, period
                        high, high_idx = price, period # reset the high
                        data[period]['new_low'] = price

                    # Find new highs, including the index
                    if price > high:
                        high = price
                        high, high_idx = price, period
                        data[period]['new_high'] = price

                    # Calculate and check profit
                    profit = round((high - low)/low * 100, 2)
                    if profit > 0:
                        if profit != last_profit:
                            data[period]['profit %'] = profit
                    last_profit = profit

                    # Record the new max_profit
                    if profit > max_profit:
                        max_profit, buy, sell = profit, low_idx, high_idx
                        data[period]['new_max_profit'] = profit

                

                # Create final buy and sell action on the current period
                data[buy]['action'], data[sell]['action'] = 'buy', 'sell'
                df = pd.DataFrame(data).T
                df = df.fillna('')
                df = df[['current', 'profit %', 'new_low', 'new_high', 'new_max_profit', 'action']]

                # Filter for buy and sell action only
                actions = df[(df['action']=='buy') | (df['action']=='sell')][['current', 'profit %', 'action']]

                # Save the two dfs
                ticker_data['max_profit'] = actions
                ticker_data['max_profit_history'] = df

            except AttributeError:
                raise AttributeError(f'No forecasting done yet for {ticker}')
            except Exception as e:
                raise Exception(e)
            
    def find_best_trades(self, *args):
        '''
        Finds all the trades and returns best n trades
        Parameters:
            ticker (str) : ticker to plot from stored forecast
        '''
        if not args:
            args = self.tickers.keys()

        for ticker in args:
            try:
                ticker_data = self.tickers.get(ticker, None)     
                forecast = ticker_data.get('forecast', None)  
                low = None
                data = {}
                for period, price in zip(forecast.index, forecast):
                    data[period] = dict(current=price) # Saves every period as index
                    if not low:
                        # Initial assignments
                        low, low_idx = price, period
                        first_decline = False
                    else:
                        if price >= last_price:
                            first_decline = True # To reset the memory on whether there has ever been a decline

                        elif price < last_price:
                            if first_decline:
                                # Determine to sell if the current period price is a first drop
                                data[last_idx]['action'] = 'sell'

                                # Calculations
                                profit = round((last_price - low)/low * 100, 2)
                                hold_period = (last_idx - low_idx).n

                                # Record
                                data[last_idx]['profit %'] = profit
                                data[last_idx]['hold period'] = hold_period
                                data[low_idx]['action'] = 'buy'
                                first_decline = False
                            # Register the new low for next profit
                            low, low_idx = price, period

                    last_price, last_idx = price, period

                df = pd.DataFrame(data).T
                df = df.fillna('')
                df = df[['current', 'profit %', 'action', 'hold period']]

                # Filter for buy and sell action only
                actions = df[(df['action']=='buy') | (df['action']=='sell')][['current', 'profit %', 'action', 'hold period']]

                # Get totals
                compounding_gains = [float(x)*0.01 + 1 for x in actions['profit %'].to_list() if x != '']
                total_gain = round((np.prod(compounding_gains)-1)*100 , 2)
                hold_periods = [int(x) for x in actions['hold period'].to_list() if x != '']
                total_hold_period = sum(hold_periods)

                actions.loc[len(actions.index)] = ['Compound gain', total_gain, '', total_hold_period]  

                # Save the two dfs
                ticker_data['best_trades'] = actions
                ticker_data['best_trades_history'] = df
                

            except AttributeError:
                raise AttributeError(f'No forecasting done yet for {ticker}')
            except Exception as e:
                raise Exception(e)
