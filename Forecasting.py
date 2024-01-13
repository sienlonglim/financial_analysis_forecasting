from modules.utils import logger
from modules.YfScrapper import *
from modules.Forecaster import *
import streamlit as st

@st.cache_resource
def initialize(name: str):
    if name not in st.session_state:
        if name == 'Forecaster':
            instance = st.session_state['Forecaster'] = Forecaster()
        if name == 'Scrapper':
            instance = st.session_state['Scrapper'] = YfScrapper()
        logger.info('----------Started New Run----------------')
        logger.info(f'{instance} initiated')
    return instance

def main():
    st.set_page_config(page_title='Financial Analysis by Sien Long')
    fc = initialize('Forecaster')

    st.header('Financial Analysis by Sien Long')
    st.write('Welcome to my app for financial analysis. The app covers three areas, click on the subpages to proceed')
    st.write('1. Time series forecasting')
    st.write('2. Segment analysis')
    st.write('3. Recommendation system')
    st.header('Seasonal ARIMA')

    with st.form("my_form"):
        ticker = st.text_input('Enter Ticker Symbol', 'SPY').upper()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            price_type = st.selectbox('Price type', ['Open', 'Close', 'High', 'Low'], 1)
            period = st.selectbox('Price history period', ['5y', '1y', 'ytd', '10y'])
        with col2:
            p = st.selectbox('p', [i for i in range(10)])
        with col3:
            d = st.selectbox('d', [i for i in range(3)], 1)
        with col4:
            q = st.selectbox('q', [i for i in range(3)], 1)
        submitted = st.form_submit_button("Forecast")
    if submitted and len(ticker)>0:
        with st.spinner('Forecasting ...'):
            fc.forecast(ticker, price_type=price_type, period=period, order=(p,d,q))
        st.line_chart(fc[ticker]['forecast'].to_timestamp())
        if st.button('View model stats'):
            st.write(fc[ticker]['model'].summary())
        if st.button('Past price'):
            st.line_chart(fc[ticker]['ts'].to_timestamp())

if __name__ == '__main__':
    main()