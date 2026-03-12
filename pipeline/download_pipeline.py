from scraper.announcement_scraper import get_announcements
from downloader.file_downloader import download_file
from utils.date_filter import filter_by_date_range
from utils.financial_filter import is_financial_announcement
from utils.announcement_classifier import classify_announcement

from pathlib import Path
import time
import re
from datetime import datetime


# ---------------- QUARTER DETECTION ----------------

def detect_quarter(item):

    text = ""

    if item.get("desc"):
        text += " " + item["desc"]

    if item.get("attchmntText"):
        text += " " + item["attchmntText"]

    if item.get("attchmntFile"):
        text += " " + item["attchmntFile"]

    text = text.lower()

    # Pattern like Q1 FY25
    match = re.search(r"q([1-4])\s*fy\s*([0-9]{2,4})", text)

    if match:

        q = match.group(1)
        fy = match.group(2)

        if len(fy) == 2:
            fy = "20" + fy

        return f"FY{fy}_Q{q}"

    # Pattern: quarter ended month
    month_map = {
        "march": "Q4",
        "june": "Q1",
        "september": "Q2",
        "december": "Q3"
    }

    for month in month_map:

        if month in text:

            q = month_map[month]

            try:
                dt = datetime.strptime(item["an_dt"], "%d-%b-%Y %H:%M:%S")
                fy = dt.year
            except:
                fy = datetime.now().year

            return f"FY{fy}_{q}"

    # fallback: use announcement date
    try:

        dt = datetime.strptime(item["an_dt"], "%d-%b-%Y %H:%M:%S")

        month = dt.month

        if month <= 3:
            q = "Q4"
        elif month <= 6:
            q = "Q1"
        elif month <= 9:
            q = "Q2"
        else:
            q = "Q3"

        return f"FY{dt.year}_{q}"

    except:

        return "Unknown_Period"


# ---------------- ANNOUNCEMENT CHECK ----------------

def check_announcements(symbol, start_date=None, end_date=None):

    announcements = get_announcements(symbol)

    if not announcements:
        return [], 0, 0, 0

    total_announcements = len(announcements)

    # Apply date filter
    if start_date or end_date:
        announcements = filter_by_date_range(announcements, start_date, end_date)

    filtered_count = len(announcements)

    # Keep only financial announcements
    financial_announcements = []

    for item in announcements:

        if is_financial_announcement(item):
            financial_announcements.append(item)

    financial_count = len(financial_announcements)

    return financial_announcements, total_announcements, filtered_count, financial_count


# ---------------- DOWNLOAD REPORTS ----------------

def download_reports(symbol, announcements, limit):

    downloads_folder = Path.home() / "Downloads"
    base_folder = downloads_folder / "FinanceAnalyzer" / symbol

    base_folder.mkdir(parents=True, exist_ok=True)

    count = 0
    downloaded_keys = set()
    downloaded_files = set()

    for item in announcements[:limit]:

        if "attchmntFile" not in item or not item["attchmntFile"]:
            continue

        url = item["attchmntFile"]

        if not url.startswith("http"):
            url = "https://nsearchives.nseindia.com/" + url

        # -------- NEW: skip non-pdf files --------

        if not url.lower().endswith(".pdf"):
            continue

        category = classify_announcement(item)

        desc = (item.get("desc") or "").lower()

        skip_words = [
            "newspaper publication",
            "copy of newspaper",
            "advertisement",
            "press release",
            "press note"
        ]

        if any(w in desc for w in skip_words):
            continue

        date_key = item.get("an_dt", "")
        unique_key = f"{category}_{date_key}"

        if unique_key in downloaded_keys:
            continue

        downloaded_keys.add(unique_key)

        filename = url.split("/")[-1]

        # -------- NEW: duplicate filename protection --------

        if filename in downloaded_files:
            continue

        downloaded_files.add(filename)

        # ---------- quarter folder ----------

        period = detect_quarter(item)

        folder = base_folder / period / category

        folder.mkdir(parents=True, exist_ok=True)

        try:

            success = download_file(url, folder)

            if success:
                count += 1

        except Exception:
            continue

        # small delay so NSE doesn't block requests
        time.sleep(1)

    return count