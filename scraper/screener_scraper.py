import requests
from bs4 import BeautifulSoup

def get_screener_data(company_name):

    url = f"https://www.screener.in/company/{company_name}/consolidated/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("❌ Screener fetch failed")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    # 🔥 FIXED TABLE SELECTION
    tables = soup.find_all("table", {"class": "data-table"})

    for table in tables:

        heading = table.find_previous("h2")

        if heading and "Quarterly Results" in heading.text:

            rows = table.find_all("tr")

            for row in rows:

                cols = [c.text.strip() for c in row.find_all(["td", "th"])]

                if len(cols) < 2:
                    continue

                key = cols[0].lower()
                values = cols[1:]

                if "sales" in key or "revenue" in key:
                    data["revenue"] = values

                if "net profit" in key:
                    data["profit"] = values

    return data


def clean_financial_data(data):

    import re

    revenue = []
    profit = []

    for val in data.get("revenue", []):
        num = re.sub(r"[^\d.]", "", val)
        revenue.append(float(num) if num else 0)

    for val in data.get("profit", []):
        num = re.sub(r"[^\d.]", "", val)
        profit.append(float(num) if num else 0)

    return revenue, profit