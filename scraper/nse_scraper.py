import requests

def get_company_info(symbol):

    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session = requests.Session()

    # first request to get cookies
    session.get("https://www.nseindia.com", headers=headers)

    response = session.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data")
        return None