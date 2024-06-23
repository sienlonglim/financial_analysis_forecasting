class Definitions:
    REQUEST_HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    TICKER_METRICS_MAPPING = {
            'Market Cap (intraday)': 'Market Cap (B)',
            'Enterprise Value': 'Enterprise Value (B)',
            '52-Week Change': '52 Week Change (%)',
            'S&P500 52-Week Change': 'S&P500 52-Week Change (%)',
            'Avg Vol 3 month': 'Avg Vol 3 month (B)',
            'Avg Vol (10 day)': 'Avg Vol 10 day (B)',
            'Shares Short': 'Shares Short (M) (prior month)',
            'Forward Annual Dividend Yield': 'Forward Annual Dividend Yield (%)',
            'Trailing Annual Dividend Yield' : 'Trailing Annual Dividend Yield (%)',
            'Payout Ratio': 'Payout Ratio (%)',
            'Last Split Factor': 'Last Split Factor (x:1)',
            'Profit Margin': 'Profit Margin (%)',
            'Operating Margin (ttm)': 'Operating Margin (ttm) (%)',
            'Return on Assets (ttm)': 'Return on Assets (ttm) (%)',
            'Return on Equity (ttm)': 'Return on Equity (ttm) (%)',
            'Revenue (ttm)': 'Revenue (ttm) (B)',
            'Quarterly Revenue Growth (yoy)': 'Quarterly Revenue Growth (yoy) (%)',
            'Gross Profit (ttm)': 'Gross Profit (ttm) (B)',
            'EBITDA': 'EBITDA (B)',
            'Net Income Avi to Common (ttm)': 'Net Income Avi to Common (ttm) (B)',
            'Quarterly Earnings Growth (yoy)': 'Quarterly Earnings Growth (yoy) (%)',
            'Total Cash (mrq)':'Total Cash (mrq) (B)',
            'Total Debt (mrq)':'Total Debt (mrq) (B)',
            'Operating Cash Flow (ttm)': 'Operating Cash Flow (ttm) (B)',
            'Levered Free Cash Flow (ttm)': 'Levered Free Cash Flow (ttm) (B)'
        }
    PRICE_TYPES = ('Open', 'Close', 'High', 'Low')
    TIME_PERIODS = ('5y', '1y', 'ytd', '10y')
    TIME_INTERVALS = ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1wk', '1d', '5d', '1wk', '1mo', '3mo')
