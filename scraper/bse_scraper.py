import requests
import xml.etree.ElementTree as ET


def get_bse_announcements(symbol):

    announcements = []

    try:

        url = "https://www.bseindia.com/markets/MarketInfo/BSEFeeds/News.xml"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return []

        root = ET.fromstring(r.content)

        for item in root.findall(".//item"):

            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub = item.findtext("pubDate", "")

            if symbol.upper() in title.upper():

                announcements.append({
                    "desc": title,
                    "an_dt": pub,
                    "attchmntFile": link
                })

    except:
        pass

    return announcements