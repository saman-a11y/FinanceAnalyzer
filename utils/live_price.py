import requests

def get_nse_price(symbol):

    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)

        response = session.get(url, headers=headers, timeout=5)

        data = response.json()

        price = data["priceInfo"]["lastPrice"]
        high = data["priceInfo"]["intraDayHighLow"]["max"]
        low = data["priceInfo"]["intraDayHighLow"]["min"]

        return price, high, low

    except Exception as e:
        print("NSE ERROR:", e)
        return None, None, None