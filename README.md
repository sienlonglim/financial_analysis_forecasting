## Upcoming works
1. To build time series forecaster onto Streamlit next
2. Consider use of other databases (DuckDB, PostgresSQL) for learning

# Part 1 Time Series analysis and forecasting:
This script aims to perform SARIMA to analyse stock prices and forecast into the future with the following purposes:
1. Identify near-term price movement trends
2. Determine optimal actions for maximum gain
<img src="images/validation.png">
<img src="images/forecast.png">

# Part 2 Web scrapper:

<p>The web scrapper utilises BeautifulSoup 4 to scrap info from the yahoo finance statistics page.</p>
<a href = "https://finance.yahoo.com/quote/TSLA/key-statistics?p=TSLA"><img src="images/sample.JPG"></a>
<p>Two sets of data are utilized: S&P constituents and a personal portfolio.</p>

# Part 3 S&P and personal portfolio segment analysis with recommendations:

This script performs a K-means clustering on the S&P constituents to determine different groups of companies. 
The following features are used in K means clustering:
1. Market cap
2. Revenue
3. Profit Margin
4. 52 Week Change
5. Quarterly Earnings Growth (yoy)

<img src="images/s&p_clusters.jpg">

The identified clusters are compared with one's portfolio for comparison.

<img src="images/cluster_differences.jpg">

# Improvement logs:
20240110:
1. Added RMSE or AIC into TS validation
2. Optimized for SARIMA parameters, using auto_arima and further analysis

20240108:
1. Modularising Forecaster on notebook
2. Added functions to 
    - forecast
    - validate forecast
    - plot forecast
    - determine single buy and sell for maximum profit within forecast

20240107:
1. Completed modularisation of YfScrapper
2. Completed learning on time series (ARIMA, SARIMA)

20240103:
1. Refactored code and directory to modularise scrapper
2. Renamed project


