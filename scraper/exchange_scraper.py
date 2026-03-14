from scraper.announcement_scraper import get_announcements as get_nse_announcements
from scraper.bse_scraper import get_bse_announcements


# we will add BSE later
def get_all_announcements(symbol):

    try:
        nse_announcements = get_nse_announcements(symbol)
    except:
        nse_announcements = []

    # placeholder for BSE
    try:
        bse_announcements = get_bse_announcements(symbol)
    except:
        bse_announcements = []

    
    merged = nse_announcements + bse_announcements
    print("Exchange scraper merging NSE + BSE")
    print("NSE ANNOUNCEMENTS:", len(nse_announcements))
    print("BSE ANNOUNCEMENTS:", len(bse_announcements))

    # -------- REMOVE DUPLICATES --------

    
    print("TOTAL ANNOUNCEMENTS BEFORE MERGE:", len(merged))
    unique = {}

    for item in merged:

        key = (
            str(item.get("desc","")) +
            str(item.get("an_dt","")) +
            str(item.get("attchmntFile",""))
        )

        if key not in unique:
            unique[key] = item
    print("TOTAL ANNOUNCEMENTS AFTER DEDUP:", len(unique))
    return list(unique.values())