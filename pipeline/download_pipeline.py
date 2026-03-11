from scraper.announcement_scraper import get_announcements
from downloader.file_downloader import download_file
from utils.date_filter import filter_by_date_range
from utils.financial_filter import is_financial_announcement
from utils.announcement_classifier import classify_announcement

from pathlib import Path
import time


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


def download_reports(symbol, announcements, limit):

    downloads_folder = Path.home() / "Downloads"
    base_folder = downloads_folder / "FinanceAnalyzer" / symbol

    # Create base folder automatically for new users
    base_folder.mkdir(parents=True, exist_ok=True)

    count = 0

    for item in announcements[:limit]:

        if "attchmntFile" not in item or not item["attchmntFile"]:
            continue

        url = item["attchmntFile"]

        if not url.startswith("http"):
            url = "https://nsearchives.nseindia.com/" + url

        # Determine category
        category = classify_announcement(item)

        folder = base_folder / category

        # Ensure category folder exists
        folder.mkdir(parents=True, exist_ok=True)

        try:
            success = download_file(url, folder)
            if success:
                count += 1

        except Exception:
            # skip broken downloads
            continue

        # small delay so NSE doesn't block requests
        time.sleep(1)

    return count