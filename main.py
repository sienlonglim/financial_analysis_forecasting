from modules.utils import logger
from modules.YfScrapper import *
from modules.Forecaster import *
import streamlit as st

def main():
    # scrapper = YfScrapper()
    st.header('Time Series Forecasting')
    if "" not in st.session_state:
        fc = st.session_state['Forecaster'] = Forecaster()
    with st.form("my_form"):
        ticker = st.text_input('Enter Ticker Symbol').upper()
        submitted = st.form_submit_button("Forecast")
    if submitted and len(ticker)>0:
        with st.spinner('Forecasting ...'):
            fc.forecast(ticker)
            fc.find_max_profit()
        st.success('Done!')
        df = fc[ticker]['max_profit_history']
        st.dataframe(data=df)  

if __name__ == '__main__':
    main()