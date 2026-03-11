import sys
from pathlib import Path
import requests
import io
import zipfile

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from datetime import datetime
import pandas as pd
from collections import Counter
import plotly.express as px
import yfinance as yf
from streamlit_option_menu import option_menu

from pipeline.download_pipeline import check_announcements
from utils.announcement_classifier import classify_announcement

from dashboard.components.ticker import show_ticker
from dashboard.components.orderbook import show_orderbook


st.set_page_config(
    page_title="Finance Analyzer",
    page_icon="📊",
    layout="wide"
)


# ---------------- UI STYLE ----------------

st.markdown("""
<style>

body{
background-color:#0b0f19;
}

[data-testid="metric-container"]{
background:rgba(255,255,255,0.05);
backdrop-filter: blur(10px);
border-radius:12px;
padding:15px;
}

.stButton>button{
background:linear-gradient(90deg,#00d4ff,#0099ff);
border-radius:10px;
color:black;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)


# ---------------- ZIP CREATOR ----------------

def create_zip(symbol, reports):

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

        for report in reports:

            url = report.get("attchmntFile")

            if not url:
                continue

            try:

                headers = {"User-Agent": "Mozilla/5.0"}

                response = requests.get(url, headers=headers, timeout=20)

                if response.status_code != 200:
                    continue

                category = classify_announcement(report)

                filename = url.split("/")[-1]

                path = f"{symbol}/{category}/{filename}"

                zip_file.writestr(path, response.content)

            except:
                continue

    zip_buffer.seek(0)

    return zip_buffer


# ---------------- NSE SYMBOL LOADER ----------------

@st.cache_data
def load_nse_symbols():

    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:

        response = requests.get(url, headers=headers, timeout=10)

        from io import StringIO
        df = pd.read_csv(StringIO(response.text))

        df.columns = [c.strip().upper() for c in df.columns]

        df = df[["SYMBOL","NAME OF COMPANY"]]

        df["display"] = df["SYMBOL"] + " — " + df["NAME OF COMPANY"]

        return df

    except:
        return pd.DataFrame()


symbols_df = load_nse_symbols()


def resolve_symbol(user_input):

    if symbols_df.empty:
        return pd.DataFrame()

    user_input = user_input.lower()

    match = symbols_df[
        symbols_df["NAME OF COMPANY"].str.lower().str.contains(user_input, na=False)
        | symbols_df["SYMBOL"].str.lower().str.contains(user_input, na=False)
    ]

    return match.head(10)


# ---------------- NAVIGATION ----------------

selected = option_menu(
    None,
    ["Dashboard","Reports","Downloads"],
    icons=["graph-up","file-earmark","download"],
    orientation="horizontal"
)

show_ticker()


# ---------------- SESSION ----------------

if "announcements" not in st.session_state:
    st.session_state.announcements = []

if "selected_reports" not in st.session_state:
    st.session_state.selected_reports = []

if "symbol" not in st.session_state:
    st.session_state.symbol = None


# ---------------- LOGIN ----------------

password = st.text_input("Enter Password", type="password")

if password != "finance123":
    st.warning("Enter password to continue")
    st.stop()

st.success("Access granted")


# ==================================================
# DASHBOARD
# ==================================================

if selected == "Dashboard":

    st.title("📊 Finance Analyzer Terminal")

    search = st.text_input("Search Company")

    if search:

        matches = resolve_symbol(search)

        if not matches.empty:

            selected_company = st.selectbox(
                "Select Company",
                matches["display"]
            )

            st.session_state.symbol = selected_company.split(" — ")[0]

            st.success(f"Detected Symbol: {st.session_state.symbol}")

    if st.session_state.symbol:

        symbol = st.session_state.symbol + ".NS"

        try:

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")

            price = round(hist["Close"].iloc[-1],2)
            high_52w = round(hist["High"].max(),2)
            low_52w = round(hist["Low"].min(),2)

        except:

            price = "N/A"
            high_52w = "N/A"
            low_52w = "N/A"

        col1,col2,col3 = st.columns(3)

        col1.metric("Current Price",price)
        col2.metric("52W High",high_52w)
        col3.metric("52W Low",low_52w)

        try:

            history = ticker.history(period="6mo")

            fig = px.line(history,x=history.index,y="Close")

            st.plotly_chart(fig,use_container_width=True)

        except:
            st.warning("Price chart unavailable")

        show_orderbook()


# ==================================================
# REPORTS
# ==================================================

if selected == "Reports":

    st.title("📑 Financial Reports Explorer")

    search = st.text_input("Search Company")

    if search:

        matches = resolve_symbol(search)

        if not matches.empty:

            selected_company = st.selectbox(
                "Select Company",
                matches["display"]
            )

            st.session_state.symbol = selected_company.split(" — ")[0]


    col1,col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date")

    with col2:
        end_date = st.date_input("End Date")


    if st.button("Fetch Reports"):

        announcements,total,filtered,financial = check_announcements(
            st.session_state.symbol,
            datetime.combine(start_date,datetime.min.time()),
            datetime.combine(end_date,datetime.min.time())
        )

        st.session_state.announcements = announcements
        st.session_state.total = total
        st.session_state.filtered = filtered
        st.session_state.financial = financial


    if len(st.session_state.announcements) > 0:

        col1,col2,col3 = st.columns(3)

        col1.metric("Total NSE Announcements",st.session_state.total)
        col2.metric("Filtered Range",st.session_state.filtered)
        col3.metric("Financial Reports",st.session_state.financial)


        announcements = st.session_state.announcements

        categories = [classify_announcement(a) for a in announcements]

        chart_data = pd.DataFrame({
            "Category": list(Counter(categories).keys()),
            "Count": list(Counter(categories).values())
        })

        fig = px.pie(chart_data,names="Category",values="Count")

        st.plotly_chart(fig,use_container_width=True)


        # GROUP REPORTS

        category_groups = {}

        for item in announcements:

            category = classify_announcement(item)

            category_groups.setdefault(category,[]).append(item)


        selected_reports = []

        st.subheader("Select Reports")

        for category,items in category_groups.items():

            with st.expander(category.replace("_"," ").title()):

                select_all = st.checkbox(f"Select all {category}")

                for report in items[:20]:

                    label = f"{report.get('an_dt')} — {report.get('desc')}"

                    if select_all or st.checkbox(label):

                        selected_reports.append(report)

        st.session_state.selected_reports = selected_reports


        # DOWNLOAD SECTION

        st.divider()
        st.subheader("Download Reports")

        if selected_reports:

            zip_file = create_zip(st.session_state.symbol,selected_reports)

            st.download_button(
                "Download Selected Reports (ZIP)",
                data=zip_file,
                file_name=f"{st.session_state.symbol}_reports.zip",
                mime="application/zip"
            )


        if st.button("Prepare All Reports ZIP"):

            st.session_state.full_zip = create_zip(
                st.session_state.symbol,
                st.session_state.announcements
            )


        if "full_zip" in st.session_state:

            st.download_button(
                "Download All Reports (ZIP)",
                data=st.session_state.full_zip,
                file_name=f"{st.session_state.symbol}_all_reports.zip",
                mime="application/zip"
            )


# ==================================================
# DOWNLOAD MANAGER
# ==================================================

if selected == "Downloads":

    st.title("Download Manager")

    st.info("Downloads will appear in your browser's Downloads folder.")