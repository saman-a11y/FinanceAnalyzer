import streamlit as st
import yfinance as yf


def show_ticker():

    tickers = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

    text = ""

    for t in tickers:

        data = yf.Ticker(t).history(period="1d")

        if not data.empty:

            price = data["Close"].iloc[-1]
            open_price = data["Open"].iloc[-1]

            change = ((price-open_price)/open_price)*100

            arrow = "▲" if change > 0 else "▼"

            text += f"{t.replace('.NS','')} {arrow} {round(change,2)}%  |  "

    st.markdown(
        f"""
        <marquee style="color:#00d4ff;font-weight:bold;">
        {text}
        </marquee>
        """,
        unsafe_allow_html=True
    )