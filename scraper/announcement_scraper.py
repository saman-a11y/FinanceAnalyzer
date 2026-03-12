import requests
import time
import streamlit as st


# Persistent NSE session
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9"
}

# Warm NSE session (important for cookies)
try:
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    time.sleep(1)
except:
    pass


@st.cache_data(ttl=600)
def get_announcements(symbol):

    base_url = "https://www.nseindia.com"
    api_url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"

    max_retries = 3

    for attempt in range(max_retries):

        try:

            response = session.get(api_url, headers=headers, timeout=10)

            if response.status_code != 200:

                print("API failed:", response.status_code)

                time.sleep(1)
                continue

            data = response.json()

            # Sometimes NSE returns wrapped JSON
            if isinstance(data, dict):

                if "data" in data:
                    return data["data"]

            # If API returns list directly
            if isinstance(data, list):
                return data

            return []

        except Exception as e:

            print("Scraper retry:", attempt + 1)

            time.sleep(1)

    print("Scraper failed after retries")

    return []