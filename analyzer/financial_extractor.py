import re

def extract_financial_data(text):

    results = {}

    revenue_pattern = r"revenue.*?([\d,]+)"
    profit_pattern = r"net profit.*?([\d,]+)"
    eps_pattern = r"eps.*?([\d\.]+)"

    revenue = re.search(revenue_pattern, text, re.IGNORECASE)
    profit = re.search(profit_pattern, text, re.IGNORECASE)
    eps = re.search(eps_pattern, text, re.IGNORECASE)

    if revenue:
        results["Revenue"] = revenue.group(1)

    if profit:
        results["Net Profit"] = profit.group(1)

    if eps:
        results["EPS"] = eps.group(1)

    return results