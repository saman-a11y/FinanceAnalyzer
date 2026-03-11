import streamlit as st
import yfinance as yf


@st.cache_data(ttl=300)
def get_price(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d")

        if data.empty:
            return None

        return round(data["Close"].iloc[-1], 2)

    except:
        return None


def show_ticker():

    tickers = [
        ("RELIANCE.NS","RELIANCE"),
        ("TCS.NS","TCS"),
        ("INFY.NS","INFY"),
        ("HDFCBANK.NS","HDFCBANK"),
        ("ICICIBANK.NS","ICICIBANK")
    ]

    cols = st.columns(len(tickers))

    for i,(symbol,label) in enumerate(tickers):

        price = get_price(symbol)

        if price:
            cols[i].metric(label, price)
        else:
            cols[i].metric(label, "—")