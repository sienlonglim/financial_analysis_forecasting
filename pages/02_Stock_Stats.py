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
    scrapper = initialize('Scrapper')

    st.header('Ticker Statistics')
    with st.form("my_form"):
        tickers = st.text_input('Enter Ticker Symbols (separate by ,)', 'TSLA').upper()
        submitted = st.form_submit_button("Get stats")
    if submitted and len(tickers)>0:
        with st.spinner('Getting stats from YF ...'):
            tickers = [ticker.strip() for ticker in tickers.split(',')]
            scrapper.add_tickers(tickers)
            scrapper.get_ticker_stats('all', clean_df=True)
            if len(tickers)==1:
                df = scrapper[tickers[0]]
            else:
                df = scrapper.compile_dataframes().T
            st.dataframe(df, width=800, height=1000)

if __name__ == '__main__':
    main()