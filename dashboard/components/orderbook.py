import streamlit as st
import pandas as pd
import numpy as np


def show_orderbook():

    prices = np.round(np.linspace(100, 101, 10), 2)

    bids = np.random.randint(100, 1000, 10)
    asks = np.random.randint(100, 1000, 10)

    df = pd.DataFrame({
        "Bid Size": bids,
        "Price": prices,
        "Ask Size": asks[::-1]
    })

    st.subheader("Market Depth")

    st.dataframe(df, use_container_width=True)