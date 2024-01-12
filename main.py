from modules.utils import logger
from modules.YfScrapper import *
from modules.Forecaster import *
import streamlit as st

@st.cache_resource
def initialize():
    if "initialized" not in st.session_state:
        fc = st.session_state['Forecaster'] = Forecaster()
        scrapper = st.session_state['Scraooer'] = YfScrapper()
        # st.session_state['logger'] = logger
        st.session_state['initialized'] = True
    return fc, scrapper

def main():
    st.set_page_config(page_title='Financial Analysis by Sien Long')
    fc, scrapper = initialize()

    st.header('Financial Analysis by Sien Long')
    st.write('Welcome to my app for financial analysis. The app covers three areas, click on the subpages to proceed')
    st.write('1. Time series forecasting')
    st.write('2. Segment analysis')
    st.write('3. Recommendation system')

    with st.form("my_form"):
        ticker = st.text_input('Enter Ticker Symbol').upper()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            price_type = st.selectbox('Price type', ['Open', 'Close', 'High', 'Low'])
            period = st.selectbox('Price history period', ['5y', '1y', 'ytd', '10y'])
        with col2:
            p = st.selectbox('p', [i for i in range(10)])
        with col3:
            d = st.selectbox('d', [i for i in range(3)])
        with col4:
            q = st.selectbox('q', [i for i in range(3)])
        submitted = st.form_submit_button("Forecast")
    if submitted and len(ticker)>0:
        with st.spinner('Forecasting ...'):
            fc.forecast(ticker, price_type=price_type, period=period, order=(p,d,q))
            fc.find_max_profit()
        st.success('Done!')
        df = fc[ticker]['max_profit_history']
        st.dataframe(data=df)  

if __name__ == '__main__':
    main()