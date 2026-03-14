import requests

_bse_map = None


def load_bse_mapping():

    global _bse_map

    if _bse_map:
        return _bse_map

    url = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bseindia.com/"
    }

    mapping = {}

    try:

        r = requests.get(url, headers=headers, timeout=10)

        data = r.json()

        for row in data:

            name = row.get("scripname", "").upper()
            scrip = row.get("scripcode")

            if name and scrip:
                mapping[name] = str(scrip)

    except:
        pass

    _bse_map = mapping

    return mapping


def get_bse_scrip(symbol):

    mapping = load_bse_mapping()

    symbol = symbol.upper()

    # simple fuzzy match
    for name, code in mapping.items():

        if symbol in name:
            return code

    return None