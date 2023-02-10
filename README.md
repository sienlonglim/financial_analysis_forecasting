# Part 1 Web scrapper:

<p>The web scrapper utilises BeautifulSoup 4 to scrap info from the yahoo finance statistics page.</p>
<a href = "https://finance.yahoo.com/quote/TSLA/key-statistics?p=TSLA"><img src="sample.JPG"></a>
<p>Two sets of data are utilized: S&P constituents and a personal portfolio.</p>

# Part 2 S&P and personal portfolio segment analysis with recommendations:

This script performs a K means clustering on the S&P constituents to determine different groups of companies. 
The following features are used in K means clustering:
1. Market cap
2. Revenue
3. Profit Margin
4. 52 Week Change
5. Quarterly Earnings Growth (yoy)

The identified clusters are compared with one's portfolio for comparison.


