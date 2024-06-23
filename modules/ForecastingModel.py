from typing import Union, Any
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.dates as mdates
import pandas as pd
import numpy.typing as npt
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA

from .utils import configure_logging
from .definitions import Definitions


log = configure_logging(streaming=True)


class ForecastingModel():
    '''
    Object class to retrieve prices, forecast, and determine buy/sell actions
    '''
    def __init__(
        self,
        price_type: str = 'Close',
        time_period: str = '5y',
        time_interval: str = '1wk',
        model: str = 'SARIMA',
        **kwargs
    ) -> None:
        self.ticker_dict = {
            "ticker": None,
            "ts": None,
            "forecast": None,
            "model_fit": None
        }
        self._validate_price_parameters(
            price_type=price_type,
            time_period=time_period,
            time_interval=time_interval
        )
        self.price_type = price_type
        self.time_period = time_period
        self.time_interval = time_interval

        self.model = model.upper()
        if self.model == 'SARIMA':
            self.order = kwargs.get("order", (2, 1, 1))
            self.seasonal_order = kwargs.get("seasonal_order", (1, 1, 0, 52))

    def __repr__(self) -> str:
        '''
        Shows the main parameters of the class object
        '''
        return (
            f"ForecastingModel("
            f"price_type={self.price_type}, "
            f"time_period={self.time_period}, "
            f"time_interval={self.time_interval}, "
            f"model={self.model})"
        )

    def __getattr__(self, key: str) -> Any:
        '''
        Modified dunder method to call ticker_dict
        '''
        value = self.ticker_dict.get(key)
        if value is not None:
            return value
        else:
            raise ValueError('Attribute not available, '
                             'should be one of '
                             f'{", ".join(self.ticker_dict.keys())}')

    @staticmethod
    def _validate_ticker_symbol(
        ticker_symbol: str
    ) -> str:
        ticker_symbol = ticker_symbol.upper()
        if isinstance(ticker_symbol, str) and len(ticker_symbol) <= 4:
            return ticker_symbol
        else:
            raise ValueError(f"Invalid ticker given: {ticker_symbol}")

    @staticmethod
    def _validate_price_parameters(
        price_type: str,
        time_period: str,
        time_interval: str,
    ) -> None:
        if price_type not in Definitions.PRICE_TYPES:
            raise ValueError(f"price_type must be one of {', '.join(Definitions.PRICE_TYPES)}")
        if time_period not in Definitions.TIME_PERIODS:
            raise ValueError(f"period must be one of {', '.join(Definitions.TIME_PERIODS)}")
        if time_interval not in Definitions.TIME_INTERVALS:
            raise ValueError(f"interval must be one of {', '.join(Definitions.TIME_INTERVALS)}")

    def get_stock_price(
        self,
        ticker_symbol: str,
        **kwargs
    ) -> pd.DataFrame:
        price_type = kwargs.get("price_type", self.price_type)
        time_period = kwargs.get("time_period", self.time_period)
        time_interval = kwargs.get("time_interval", self.time_interval)
        
        stock = yf.Ticker(ticker_symbol)
        ts = stock.history(
            period=time_period,
            interval=time_interval
        )
        return ts[[price_type]].tz_localize(None)

    def forecast_stock_price(
        self,
        ticker_symbol: str,
        predict_start: Union[int, str, datetime],
        predict_end: Union[int, str, datetime],
        ts: npt.ArrayLike = None,
        save_results: bool = True,
        **kwargs
    ) -> None:
        ticker_symbol = self._validate_ticker_symbol(ticker_symbol)
        price_type = kwargs.get("price_type", self.price_type)
        time_period = kwargs.get("time_period", self.time_period)
        time_interval = kwargs.get("time_interval", self.time_interval)

        if ts is None:
            ts = self.get_stock_price(
                ticker_symbol,
                price_type=price_type,
                time_period=time_period,
                time_interval=time_interval
            )

        if self.model == "SARIMA":
            order = kwargs.get("order", self.order)
            seasonal_order = kwargs.get("seasonal_order", self.seasonal_order)
            log.info(f"pdq={order}, PDQm={seasonal_order}")
            model = ARIMA(
                ts,
                order=order,
                seasonal_order=seasonal_order
            )
            model_fit = model.fit()
            forecast = model_fit.predict(
                start=predict_start,
                end=predict_end,
                dynamic=False
            )
        if save_results:
            self.ticker_dict["ticker"] = ticker_symbol
            self.ticker_dict["ts"] = ts
            self.ticker_dict["forecast"] = forecast
            self.ticker_dict["model_fit"] = model_fit
        return forecast

    # WIP
    # def step_through_forecast(
    #     self,
    #     ticker_symbol: str,
    #     start: Union[int, str, datetime],
    #     end: Union[int, str, datetime],
    #     **kwargs
    # ) -> tuple:
    #     price_type = kwargs.get("price_type", self.price_type)
    #     time_period = kwargs.get("time_period", self.time_period)
    #     time_interval = kwargs.get("time_interval", self.time_interval)

    #     ts = self.get_stock_price(
    #             ticker_symbol,
    #             price_type=price_type,
    #             time_period=time_period,
    #             time_interval=time_interval
    #         )
    #     for start, end in :
    #         ts_cut = 
    #         forecast = self.forecast_stock_price(
    #             ticker_symbol,
    #             predict_start=,
    #             predict_end=,
    #             ts=ts_cut
    #             save_results=False
    #         )
    #     return forecast_full

    def plot_forecast(
        self,
        forecast_only: bool = False
    ) -> matplotlib.figure.Figure:
        if self.ticker_dict.get("forecast") is None:
            log.info('No forecasting done yet')
        else:
            ticker_symbol = self.ticker_dict['ticker']
            ts = self.ticker_dict['ts']
            forecast = self.ticker_dict['forecast']

            fig, ax = plt.subplots(1, 1, figsize=(14, 6))
            ax.set_title(f'Forecast for {ticker_symbol}')
            ax.plot(forecast, color='salmon', label='Forecast')

            if forecast_only:
                ax.tick_params(which='major', length=5, labelrotation=90)
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
                ax.tick_params(which='minor')
                ax.xaxis.set_minor_locator(mdates.DayLocator(bymonthday=(1, 8, 16, 24)))
            if not forecast_only:
                ax.plot(ts, color='grey', label='Actual')
                ax.tick_params(which='major', length=5, labelrotation=90)
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
                ax.tick_params(which='minor', labelsize=7, labelrotation=90)
                ax.xaxis.set_minor_locator(mdates.MonthLocator())
                ax.xaxis.set_minor_formatter(mdates.DateFormatter("%m"))
            plt.grid(which="both")
            plt.legend()
            return fig

    # def find_max_profit(self, *args):
    #     '''
    #     Finds the maximum profit possible without trading
    #     Parameters:
    #         ticker (str) : ticker to plot from stored forecast
    #     '''
    #     if not args:
    #         args = self.tickers.keys()

    #     for ticker in args:
    #         try:
    #             ticker_data = self.tickers.get(ticker, None)     
    #             forecast = ticker_data.get('forecast', None)  
    #             max_profit = 0
    #             high, low = None, None
    #             last_profit = None
    #             data = {}
    #             for period, price in zip(forecast.index, forecast):
    #                 price = round(price, 3)
    #                 data[period] = dict(current=price) # Saves every period as index
    #                 if not low or not high:
    #                     # Initial assignments
    #                     low = high = price 
    #                     low_idx = high_idx = period
    #                     # For edge case, where new_low is the first item
    #                     data[period]['new_low'] = price

    #                 # Find new lows, including the index
    #                 if price < low:
    #                     low, low_idx = price, period
    #                     high, high_idx = price, period # reset the high
    #                     data[period]['new_low'] = price

    #                 # Find new highs, including the index
    #                 if price > high:
    #                     high = price
    #                     high, high_idx = price, period
    #                     data[period]['new_high'] = price

    #                 # Calculate and check profit
    #                 profit = round((high - low)/low * 100, 2)
    #                 if profit > 0:
    #                     if profit != last_profit:
    #                         data[period]['profit %'] = profit
    #                 last_profit = profit

    #                 # Record the new max_profit
    #                 if profit > max_profit:
    #                     max_profit, buy, sell = profit, low_idx, high_idx
    #                     data[period]['new_max_profit'] = profit

                

    #             # Create final buy and sell action on the current period
    #             data[buy]['action'], data[sell]['action'] = 'buy', 'sell'
    #             df = pd.DataFrame(data).T
    #             df = df.fillna('')
    #             df = df[['current', 'profit %', 'new_low', 'new_high', 'new_max_profit', 'action']]

    #             # Filter for buy and sell action only
    #             actions = df[(df['action']=='buy') | (df['action']=='sell')][['current', 'profit %', 'action']]

    #             # Save the two dfs
    #             ticker_data['max_profit'] = actions
    #             ticker_data['max_profit_history'] = df

    #         except AttributeError:
    #             raise AttributeError(f'No forecasting done yet for {ticker}')
    #         except Exception as e:
    #             raise Exception(e)
            
    # def find_best_trades(self, *args):
    #     '''
    #     Finds all the trades and returns best n trades
    #     Parameters:
    #         ticker (str) : ticker to plot from stored forecast
    #     '''
    #     if not args:
    #         args = self.tickers.keys()

    #     for ticker in args:
    #         try:
    #             ticker_data = self.tickers.get(ticker, None)     
    #             forecast = ticker_data.get('forecast', None)  
    #             low = None
    #             data = {}
    #             for period, price in zip(forecast.index, forecast):
    #                 price = round(price, 3)
    #                 data[period] = dict(current=price) # Saves every period as index
    #                 if not low:
    #                     # Initial assignments
    #                     low, low_idx = price, period
    #                     first_decline = False
    #                 else:
    #                     if price >= last_price:
    #                         first_decline = True # To reset the memory on whether there has ever been a decline

    #                     elif price < last_price:
    #                         if first_decline:
    #                             # Determine to sell if the current period price is a first drop
    #                             data[last_idx]['action'] = 'sell'

    #                             # Calculations
    #                             profit = round((last_price - low)/low * 100, 2)
    #                             hold_period = (last_idx - low_idx).n

    #                             # Record
    #                             data[last_idx]['profit %'] = profit
    #                             data[last_idx]['hold period'] = hold_period
    #                             data[low_idx]['action'] = 'buy'
    #                             first_decline = False
    #                         # Register the new low for next profit
    #                         low, low_idx = price, period

    #                 last_price, last_idx = price, period

    #             df = pd.DataFrame(data).T
    #             df = df.fillna('')
    #             df = df[['current', 'profit %', 'action', 'hold period']]

    #             # Filter for buy and sell action only
    #             actions = df[(df['action']=='buy') | (df['action']=='sell')][['current', 'profit %', 'action', 'hold period']]

    #             # Get totals
    #             compounding_gains = [float(x)*0.01 + 1 for x in actions['profit %'].to_list() if x != '']
    #             total_gain = round((np.prod(compounding_gains)-1)*100 , 2)
    #             hold_periods = [int(x) for x in actions['hold period'].to_list() if x != '']
    #             total_hold_period = sum(hold_periods)

    #             actions.loc[len(actions.index)] = ['Compound gain', total_gain, '', total_hold_period]  

    #             # Save the two dfs
    #             ticker_data['best_trades'] = actions
    #             ticker_data['best_trades_history'] = df
    #         except AttributeError:
    #             raise AttributeError(f'No forecasting done yet for {ticker}')
    #         except Exception as e:
    #             raise Exception(e)
