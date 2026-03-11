import requests
import time


def get_announcements(symbol):

    base_url = "https://www.nseindia.com"
    api_url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session = requests.Session()

    try:

        # Step 1: visit NSE homepage (gets cookies)
        session.get(base_url, headers=headers, timeout=10)

        time.sleep(1)

        # Step 2: call API
        response = session.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("API failed:", response.status_code)
            return []

        data = response.json()

        # Sometimes NSE returns data wrapped
        if isinstance(data, dict):

            if "data" in data:
                return data["data"]

        # If it's already list
        if isinstance(data, list):
            return data

        return []

    except Exception as e:

        print("Scraper error:", e)

        return []