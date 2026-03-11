import sys
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from datetime import datetime
import pandas as pd
from collections import Counter
import plotly.express as px
import yfinance as yf
from streamlit_option_menu import option_menu

from pipeline.download_pipeline import check_announcements, download_reports
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
                matches["display"],
                key="dashboard_company"
            )

            st.session_state.symbol = selected_company.split(" — ")[0]

            st.success(f"Detected Symbol: {st.session_state.symbol}")

        else:
            st.warning("No matching NSE company found")

    if st.session_state.symbol:

        ticker = yf.Ticker(st.session_state.symbol + ".NS")

        info = ticker.info

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Current Price", info.get("currentPrice","N/A"))
        col2.metric("Market Cap", info.get("marketCap","N/A"))
        col3.metric("PE Ratio", info.get("trailingPE","N/A"))
        col4.metric("52W High", info.get("fiftyTwoWeekHigh","N/A"))

        history = ticker.history(period="6mo")

        fig = px.line(history, x=history.index, y="Close")

        st.plotly_chart(fig, use_container_width=True)

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
                matches["display"],
                key="reports_company"
            )

            st.session_state.symbol = selected_company.split(" — ")[0]

        else:
            st.warning("No company found")


    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date")

    with col2:
        end_date = st.date_input("End Date")


    if st.button("Fetch Reports"):

        announcements, total, filtered, financial = check_announcements(
            st.session_state.symbol,
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time())
        )

        st.session_state.announcements = announcements
        st.session_state.total = total
        st.session_state.filtered = filtered
        st.session_state.financial = financial


    if len(st.session_state.announcements) > 0:

        col1, col2, col3 = st.columns(3)

        col1.metric("Total NSE Announcements", st.session_state.total)
        col2.metric("Filtered Range", st.session_state.filtered)
        col3.metric("Financial Reports", st.session_state.financial)

        announcements = st.session_state.announcements

        categories = [classify_announcement(a) for a in announcements]

        chart_data = pd.DataFrame({
            "Category": list(Counter(categories).keys()),
            "Count": list(Counter(categories).values())
        })

        fig = px.pie(chart_data, names="Category", values="Count")

        st.plotly_chart(fig, use_container_width=True)

        # ---------- GROUP BY CATEGORY ----------

        category_groups = {}

        for item in announcements:

            category = classify_announcement(item)

            if category not in category_groups:
                category_groups[category] = []

            category_groups[category].append(item)


        selected_reports = []

        st.subheader("Select Reports")

        for category, items in category_groups.items():

            with st.expander(category.replace("_"," ").title(), expanded=True):

                select_all = st.checkbox(
                    f"Select all {category}",
                    key=f"select_{category}"
                )

                for i, report in enumerate(items[:20]):

                    label = f"{report.get('an_dt')} — {report.get('desc')}"

                    if select_all:

                        selected_reports.append(report)

                    else:

                        if st.checkbox(label, key=f"{category}_{i}"):

                            selected_reports.append(report)

        st.session_state.selected_reports = selected_reports


        col1, col2 = st.columns(2)

        with col1:

            if len(selected_reports) > 0:

                if st.button("Download Selected Reports"):

                    progress = st.progress(0)

                    for i, report in enumerate(selected_reports):

                        download_reports(st.session_state.symbol, [report], 1)

                        progress.progress((i + 1) / len(selected_reports))

                    st.success("Reports downloaded successfully")

        with col2:

            if st.button("Download All Reports"):

                progress = st.progress(0)

                for i, report in enumerate(announcements):

                    download_reports(st.session_state.symbol, [report], 1)

                    progress.progress((i + 1) / len(announcements))

                st.success("All reports downloaded")


# ==================================================
# DOWNLOAD MANAGER
# ==================================================

if selected == "Downloads":

    st.title("Download Manager")

    download_path = Path.home() / "Downloads" / "FinanceAnalyzer"

    if download_path.exists():

        files = list(download_path.rglob("*.pdf"))

        recent = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]

        st.subheader("Recent Downloads")

        for f in recent:
            st.write("📄", f.name)

    else:

        st.info("No downloads yet.")