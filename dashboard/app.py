import sys
from pathlib import Path
import requests
import io
import zipfile
import tempfile

# Allow importing project modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.download_pipeline import detect_quarter
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

from analyzer.financial_extractor import extract_financial_summary, generate_ai_summary
from analyzer.pdf_reader import preview_pdf


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

        symbol = st.session_state.symbol + ".NS"

        try:

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")

            if not hist.empty:

                price = round(hist["Close"].iloc[-1],2)
                high_52w = round(hist["High"].max(),2)
                low_52w = round(hist["Low"].min(),2)

            else:

                price = "N/A"
                high_52w = "N/A"
                low_52w = "N/A"

        except:

            price = "N/A"
            high_52w = "N/A"
            low_52w = "N/A"

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Price", price)
        col2.metric("52W High", high_52w)
        col3.metric("52W Low", low_52w)

        try:

            history = ticker.history(period="6mo")

            fig = px.line(
                history,
                x=history.index,
                y="Close",
                title=f"{st.session_state.symbol} Price Chart"
            )

            st.plotly_chart(fig, use_container_width=True)

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

        if not st.session_state.symbol:
            st.warning("Please select a company first.")
            st.stop()

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

        announcements = st.session_state.announcements

        col1, col2, col3 = st.columns(3)

        col1.metric("Total NSE Announcements", st.session_state.total)
        col2.metric("Filtered Range", st.session_state.filtered)
        col3.metric("Financial Reports", st.session_state.financial)

        categories = [classify_announcement(a) for a in announcements]

        chart_data = pd.DataFrame({
            "Category": list(Counter(categories).keys()),
            "Count": list(Counter(categories).values())
        })

        fig = px.pie(chart_data, names="Category", values="Count")
        st.plotly_chart(fig, use_container_width=True)


        # -------- CATEGORY GROUPING --------

        category_groups = {}

        for item in announcements:

            category = classify_announcement(item)

            category_groups.setdefault(category, []).append(item)


        selected_reports = []

        st.subheader("Select Reports")

        for category, items in category_groups.items():

            with st.expander(category.replace("_"," ").title(), expanded=True):

                select_all = st.checkbox(
                    f"Select all {category}",
                    key=f"select_{category}"
                )

                for i, report in enumerate(items):

                    label = f"{report.get('an_dt')} — {report.get('desc')}"

                    if select_all:
                        selected_reports.append(report)

                    else:
                        if st.checkbox(label, key=f"{category}_{i}"):
                            selected_reports.append(report)

        st.session_state.selected_reports = selected_reports
                # ---------- REPORT PREVIEW ----------

        if len(selected_reports) == 1:

            report = selected_reports[0]

            pdf_url = report.get("attchmntFile")

            if pdf_url:

                try:

                    session = requests.Session()

                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
                        "Referer": "https://www.nseindia.com/",
                        "Accept": "application/pdf"
                    }

                    # NSE needs cookies first
                    session.get("https://www.nseindia.com", headers=headers)

                    r = session.get(pdf_url, headers=headers, timeout=20)

                    if r.status_code == 200:

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(r.content)
                            pdf_path = tmp.name

                        summary = extract_financial_summary(pdf_path)

                        st.subheader("📊 Financial Summary")

                        col1, col2, col3 = st.columns(3)

                        col1.metric("Revenue", summary.get("Revenue"))
                        col2.metric("Profit", summary.get("Profit"))
                        col3.metric("EPS", summary.get("EPS"))

                        st.subheader("🧠 Auto Earnings Summary")

                        insights = generate_ai_summary(summary)

                        for i in insights:
                            st.write("•", i)

                        st.subheader("📄 Report Preview")

                        preview_text = preview_pdf(pdf_path)

                        st.text_area("Preview", preview_text, height=300)

                except Exception:

                    st.warning("Preview unavailable for this PDF")

        # ---------- DOWNLOAD BUTTONS ----------

        col1, col2 = st.columns(2)

        # ---------- DOWNLOAD SELECTED ZIP ----------

        with col1:

            if len(selected_reports) > 0:

                if st.button("Download Selected Reports (ZIP)"):

                    zip_buffer = io.BytesIO()

                    session = requests.Session()

                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://www.nseindia.com/"
                    }

                    session.get("https://www.nseindia.com", headers=headers)

                    urls = []
                    meta = []

                    for report in selected_reports:

                        pdf_url = report.get("attchmntFile")

                        if pdf_url:
                            urls.append(pdf_url)
                            meta.append(report)

                    from concurrent.futures import ThreadPoolExecutor

                    def fetch(url):
                        try:
                            r = session.get(url, headers=headers, timeout=20)
                            if r.status_code == 200:
                                return r.content
                        except:
                            return None

                    contents = []

                    with ThreadPoolExecutor(max_workers=5) as executor:
                        contents = list(executor.map(fetch, urls))

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

                        for report, content in zip(meta, contents):

                            if not content:
                                continue

                            category = classify_announcement(report)
                            period = detect_quarter(report)

                            filename = report["attchmntFile"].split("/")[-1]

                            zip_path = f"{st.session_state.symbol}/{period}/{category}/{filename}"

                            zipf.writestr(zip_path, content)

                    zip_buffer.seek(0)

                    st.download_button(
                        label="Download Selected ZIP",
                        data=zip_buffer,
                        file_name=f"{st.session_state.symbol}_selected_reports.zip",
                        mime="application/zip"
                    )


        # ---------- DOWNLOAD ALL ZIP ----------

        with col2:

            if st.button("Download All Reports (ZIP)"):

                zip_buffer = io.BytesIO()

                session = requests.Session()

                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://www.nseindia.com/"
                }

                session.get("https://www.nseindia.com", headers=headers)

                urls = []
                meta = []

                for report in announcements:

                    pdf_url = report.get("attchmntFile")

                    if pdf_url:
                        urls.append(pdf_url)
                        meta.append(report)

                from concurrent.futures import ThreadPoolExecutor

                def fetch(url):
                    try:
                        r = session.get(url, headers=headers, timeout=20)
                        if r.status_code == 200:
                            return r.content
                    except:
                        return None

                contents = []

                with ThreadPoolExecutor(max_workers=5) as executor:
                    contents = list(executor.map(fetch, urls))

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

                    for report, content in zip(meta, contents):

                        if not content:
                            continue

                        category = classify_announcement(report)
                        period = detect_quarter(report)

                        filename = report["attchmntFile"].split("/")[-1]

                        zip_path = f"{st.session_state.symbol}/{period}/{category}/{filename}"

                        zipf.writestr(zip_path, content)

                zip_buffer.seek(0)

                st.download_button(
                    label="Download All Reports ZIP",
                    data=zip_buffer,
                    file_name=f"{st.session_state.symbol}_financial_reports.zip",
                    mime="application/zip"
                )

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