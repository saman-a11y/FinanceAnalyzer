import sys
from pathlib import Path
# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from downloader.file_downloader import download_file

from scraper.screener_scraper import get_screener_data, clean_financial_data



import requests
import io
import zipfile
import tempfile
from utils.pdf_quarter_reader import extract_pdf_text_first_page

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
st.markdown("""
<style>

/* 🔥 BACKGROUND */
body {
    background: radial-gradient(circle at top left, #0f172a, #020617);
    color: #e2e8f0;
}

/* 🔥 MAIN CONTAINER */
.block-container {
    padding-top: 2rem;
}

/* 🔥 GLASS CARDS */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

/* 🔥 BUTTONS */
.stButton>button {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    border: none;
}

/* 🔥 INPUTS */
.stTextInput>div>div>input {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.1);
    color: white;
}

/* 🔥 SELECTBOX */
.stSelectbox>div>div {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}

/* 🔥 HEADINGS */
h1, h2, h3 {
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* 🔥 NAV BAR */
.css-1d391kg {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(10px);
    border-radius: 15px;
}

/* 🔥 DIVIDER */
hr {
    border: none;
    height: 1px;
    background: rgba(255,255,255,0.08);
}

</style>
""", unsafe_allow_html=True)







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
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ================= THEME SWITCH =================

theme = st.radio(
    "Theme",
    ["Dark", "Light"],
    horizontal=True
)

# ================= APPLY THEME (FINAL OVERRIDE) =================

if theme == "Dark":

    st.markdown("""
    <style>

    body {
        background: radial-gradient(circle at top left, #0f172a, #020617);
        color: #e2e8f0;
    }

    /* TEXT VISIBILITY */
    label, p, span, div {
        color: #e2e8f0 !important;
    }

    /* INPUT */
    .stTextInput input {
        background: rgba(255,255,255,0.05);
        color: white;
    }

    /* SELECT */
    .stSelectbox div {
        color: white;
    }

    </style>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <style>

    body {
        background: linear-gradient(to right, #f8fafc, #e2e8f0);
        color: #0f172a;
    }

    /* TEXT FIX (VERY IMPORTANT) */
    label, p, span, div {
        color: #0f172a !important;
    }

    /* CARDS */
    [data-testid="metric-container"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        color: black !important;
    }

    /* INPUT */
    .stTextInput input {
        background: white;
        color: black;
        border: 1px solid #cbd5e1;
    }

    /* SELECT */
    .stSelectbox div {
        color: black;
    }

    </style>
    """, unsafe_allow_html=True)

# ==================================================
# DASHBOARD
# ==================================================

if selected == "Dashboard":

    st.markdown("""
<div style="padding: 10px 5px 20px 5px;">
""", unsafe_allow_html=True)

    st.markdown(f"""
<div style="
padding: 20px;
border-radius: 18px;
background: linear-gradient(135deg, rgba(0,114,255,0.2), rgba(0,198,255,0.1));
border: 1px solid rgba(255,255,255,0.08);
margin-bottom: 20px;
">

<h1 style="margin-bottom:0;">📊 Finance Analyzer</h1>
<p style="opacity:0.7;">
{st.session_state.symbol if st.session_state.symbol else "Search a company to begin analysis"}
</p>

</div>
""", unsafe_allow_html=True)

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

        from utils.live_price import get_nse_price

        price, high_52w, low_52w = get_nse_price(st.session_state.symbol)

        # 🔥 FALLBACK TO YAHOO IF NSE FAILS
        if price is None:

            try:
                ticker = yf.Ticker(st.session_state.symbol + ".NS")
                hist = ticker.history(period="1y")

                if not hist.empty:

                    last_price = hist["Close"].dropna()

                    if len(last_price) > 0:

                        price = round(last_price.iloc[-1], 2)
                        high_52w = round(hist["High"].max(), 2)
                        low_52w = round(hist["Low"].min(), 2)

                    else:
                        price, high_52w, low_52w = "N/A", "N/A", "N/A"

                else:
                    price, high_52w, low_52w = "N/A", "N/A", "N/A"

            except:
                price, high_52w, low_52w = "N/A", "N/A", "N/A"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 💰 Price")
            st.metric("Current", price)

        with col2:
            st.markdown("### 📈 High")
            st.metric("52W High", high_52w)

        with col3:
            st.markdown("### 📉 Low")
            st.metric("52W Low", low_52w)

        try:

            ticker = yf.Ticker(st.session_state.symbol + ".NS")
            history = ticker.history(period="6mo")

            if history is not None and not history.empty:

                history = history.dropna()

                if len(history) > 0:

                    fig = px.line(
                        history,
                        x=history.index,
                        y="Close",
                        title=f"{st.session_state.symbol} Price Chart"
                    )

                    st.plotly_chart(fig, width='stretch')

                else:
                    st.warning("⚠️ No valid chart data available")

            else:
                st.warning("⚠️ Yahoo chart data unavailable")

        except Exception as e:
            print("Chart Error:", e)
            st.warning("⚠️ Price chart unavailable")


        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 📘 Order Book Insights")


        show_orderbook()


        # ================= LIVE TRADINGVIEW CHART =================

        # ================= CHART OPTIONS =================

        st.markdown("### 📈 Market Chart")

        col1, col2 = st.columns([3,1])

        with col1:
            chart_mode = st.radio(
                "Choose Chart Type",
                ["Built-in Chart", "TradingView"],
                horizontal=True
            )

        with col2:
            if st.button("Open in TradingView ↗"):
                tv_symbol = f"NSE:{st.session_state.symbol}"
                url = f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
                st.markdown(f"[Click here to open full chart]({url})")

        

        # ================= BUILT-IN CHART =================

        if chart_mode == "Built-in Chart":

            try:
                ticker = yf.Ticker(st.session_state.symbol + ".NS")

                # -------- CONTROLS --------
                colA, colB, colC = st.columns(3)

                with colA:
                    timeframe = st.selectbox(
                        "Timeframe",
                        ["1mo", "3mo", "6mo", "1y", "5y"]
                    )

                with colB:
                    show_ma = st.checkbox("Moving Averages", value=True)

                with colC:
                    show_rsi = st.checkbox("RSI Indicator")

                hist = ticker.history(period=timeframe)

                if not hist.empty:

                    import plotly.graph_objects as go
                    import pandas as pd

                    df = hist.copy()

                    # -------- INDICATORS --------

                    # Moving Averages
                    df["MA20"] = df["Close"].rolling(window=20).mean()
                    df["MA50"] = df["Close"].rolling(window=50).mean()

                    # RSI
                    delta = df["Close"].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df["RSI"] = 100 - (100 / (1 + rs))

                    # -------- MAIN CHART --------

                    fig = go.Figure()

                    # ================= CANDLESTICK =================
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        increasing_line_color="#26a69a",   # TradingView green
                        decreasing_line_color="#ef5350",   # TradingView red
                        increasing_fillcolor="#26a69a",
                        decreasing_fillcolor="#ef5350",
                        name="Price"
                    ))

                    # ================= VOLUME =================
                    fig.add_trace(go.Bar(
                        x=df.index,
                        y=df["Volume"],
                        name="Volume",
                        marker_color="rgba(100,100,100,0.3)",
                        yaxis="y2"
                    ))

                    # ================= MOVING AVERAGES =================
                    if show_ma:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df["MA20"],
                            line=dict(color="#2962ff", width=2),
                            name="MA20"
                        ))

                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df["MA50"],
                            line=dict(color="#ff6d00", width=2),
                            name="MA50"
                        ))

                    # ================= LAYOUT (THIS IS THE MAGIC) =================
                    fig.update_layout(

                        template="plotly_dark",

                        height=520,

                        margin=dict(l=20, r=20, t=20, b=20),

                        xaxis=dict(
                            showgrid=False,
                            rangeslider=dict(visible=False),   # 🔥 remove ugly slider
                        ),

                        yaxis=dict(
                            title="Price",
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.05)"
                        ),

                        yaxis2=dict(
                            title="Volume",
                            overlaying="y",
                            side="right",
                            showgrid=False,
                            position=1
                        ),

                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),

                        hovermode="x unified",   # 🔥 smooth hover like TradingView
                    )

                    # ================= CLEAN TOOLBAR =================
                    st.markdown("""
                    <div style="
                    padding:15px;
                    border-radius:15px;
                    background: rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.08);
                    ">
                    """, unsafe_allow_html=True)

                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # -------- RSI CHART --------

                    if show_rsi:

                        rsi_fig = go.Figure()

                        rsi_fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df["RSI"],
                            mode='lines',
                            name="RSI"
                        ))

                        rsi_fig.add_hline(y=70)
                        rsi_fig.add_hline(y=30)

                        rsi_fig.update_layout(
                            template="plotly_dark",
                            height=220,
                            margin=dict(l=20, r=20, t=20, b=20),
                            yaxis=dict(range=[0,100]),
                            xaxis=dict(showgrid=False),
                            hovermode="x unified"
                        )

                        st.plotly_chart(rsi_fig, width='stretch')

                else:
                    st.warning("No data available")

            except Exception as e:
                st.warning("Chart unavailable")

        # ================= TRADINGVIEW REDIRECT =================

        elif chart_mode == "TradingView":

            tv_symbol = f"NSE:{st.session_state.symbol}"

            st.info("TradingView provides full advanced charts")

            st.markdown(f"""
            👉 Click below to open:

            🔗 https://www.tradingview.com/chart/?symbol={tv_symbol}
            """)

        

        # ================= COMPANY COMPARISON =================

        st.markdown("---")
        st.subheader("📊 Compare Companies")

        col1, col2 = st.columns(2)

        with col1:
            search1 = st.text_input("Search Company 1", key="comp1_search")

            comp1 = None
            if search1:
                matches1 = resolve_symbol(search1)

                if not matches1.empty:
                    selected1 = st.selectbox(
                        "Select Company 1",
                        matches1["display"],
                        key="comp1_select"
                    )
                    comp1 = selected1.split(" — ")[0]

        with col2:
            search2 = st.text_input("Search Company 2", key="comp2_search")

            comp2 = None
            if search2:
                matches2 = resolve_symbol(search2)

                if not matches2.empty:
                    selected2 = st.selectbox(
                        "Select Company 2",
                        matches2["display"],
                        key="comp2_select"
                    )
                    comp2 = selected2.split(" — ")[0]

        # ---------------- COMPARISON ----------------

        if comp1 and comp2:

            try:
                t1 = yf.Ticker(comp1 + ".NS")
                t2 = yf.Ticker(comp2 + ".NS")

                h1 = t1.history(period="6mo")["Close"]
                h2 = t2.history(period="6mo")["Close"]

                df = pd.DataFrame({
                    comp1: h1,
                    comp2: h2
                }).dropna()

                if not df.empty:

                    fig = px.line(df, title=f"{comp1} vs {comp2}")
                    st.plotly_chart(fig, width='stretch')

                else:
                    st.warning("No comparison data available")

            except:
                st.warning("Comparison failed")
           # ================= SCREENER FINANCIALS =================

        if not st.session_state.symbol:
            st.info("Select a company to view financial trends")
            st.stop()

            
        st.subheader("📊 Financial Trends (Screener Data)")

        try:

            data = get_screener_data(st.session_state.symbol)

            if data:

                

                # ================= FINANCIAL UI (NEW) =================

                import plotly.graph_objects as go

                st.markdown("## 📊 Financial Intelligence")

                revenue, profit = clean_financial_data(data)

                # ---------------- METRICS ----------------

                if len(revenue) < 2 or len(profit) < 2:
                    st.warning("Not enough data for trend analysis")
                    st.stop()

                latest_rev = revenue[-1]
                prev_rev = revenue[-2]

                latest_profit = profit[-1]
                prev_profit = profit[-2]

                

                rev_growth = ((latest_rev - prev_rev) / prev_rev) * 100
                profit_growth = ((latest_profit - prev_profit) / prev_profit) * 100

                col1, col2 = st.columns(2)

                col1.metric(
                    "Revenue (Latest)",
                    f"{latest_rev:,.0f}",
                    f"{rev_growth:.2f}%"
                )

                col2.metric(
                    "Profit (Latest)",
                    f"{latest_profit:,.0f}",
                    f"{profit_growth:.2f}%"
                )

                st.markdown("---")

                # ---------------- CHARTS ----------------

                quarters = [f"Q{i+1}" for i in range(len(revenue))]

                # Revenue Chart
                rev_fig = go.Figure()

                rev_fig.add_trace(go.Scatter(
                    x=quarters,
                    y=revenue,
                    mode='lines+markers',
                    name='Revenue'
                ))

                rev_fig.update_layout(
                    title="Revenue Trend",
                    template="plotly_dark",
                    height=350,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(rev_fig, use_container_width=True, config={"displayModeBar": False})

                # Profit Chart
                profit_fig = go.Figure()

                profit_fig.add_trace(go.Scatter(
                    x=quarters,
                    y=profit,
                    mode='lines+markers',
                    name='Profit'
                ))

                profit_fig.update_layout(
                    title="Profit Trend",
                    template="plotly_dark",
                    height=350,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(profit_fig, use_container_width=True, config={"displayModeBar": False})

                st.markdown("---")

                # ---------------- INSIGHTS ----------------

                st.markdown("### 🧠 Insights")

                if rev_growth > 0:
                    st.success(f"Revenue growing at {rev_growth:.2f}% QoQ")
                else:
                    st.error(f"Revenue declined by {abs(rev_growth):.2f}% QoQ")

                if profit_growth > 0:
                    st.success(f"Profit increasing at {profit_growth:.2f}% QoQ")
                else:
                    st.error(f"Profit declined by {abs(profit_growth):.2f}% QoQ")

            else:
                st.warning("No Screener data found")

        except Exception as e:
            st.error(f"Screener Error: {e}")

 
st.markdown("</div>", unsafe_allow_html=True)

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

        # ================= EXPORT TO EXCEL =================

        import pandas as pd

        if len(st.session_state.selected_reports) > 0:

            export_data = []

            for r in st.session_state.selected_reports:
                export_data.append({
                    "Date": r.get("an_dt"),
                    "Description": r.get("desc"),
                    "Category": classify_announcement(r),
                    "Link": r.get("attchmntFile")
                })

            df = pd.DataFrame(export_data)

            st.download_button(
                label="📥 Export Selected Reports",
                data=df.to_csv(index=False),
                file_name=f"{st.session_state.symbol}_reports.csv",
                mime="text/csv"
            )
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

                            # -------- NEW: read PDF text for accurate quarter detection --------
                            pdf_text = ""
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                    tmp.write(content)
                                    pdf_path = tmp.name

                                pdf_text = extract_pdf_text_first_page(pdf_path)
                            except:
                                pass

                            period = detect_quarter(report, pdf_text)

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

                        pdf_text = ""
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                tmp.write(content)
                                pdf_path = tmp.name

                            pdf_text = extract_pdf_text_first_page(pdf_path)
                        except:
                            pass

                        period = detect_quarter(report, pdf_text)

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