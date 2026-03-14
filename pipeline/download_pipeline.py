from scraper.exchange_scraper import get_all_announcements as get_announcements
from downloader.file_downloader import download_file
from utils.date_filter import filter_by_date_range
from utils.financial_filter import is_financial_announcement
from utils.announcement_classifier import classify_announcement
from utils.pdf_content_classifier import validate_with_pdf

from pathlib import Path
import time
import re
from datetime import datetime
from utils.pdf_quarter_reader import extract_pdf_text_first_page
print("NEW QUARTER DETECTOR LOADED")
# ---------------- QUARTER DETECTION ----------------

def detect_quarter(item, pdf_text=None):
    
    import re
    from datetime import datetime

    text = ""
    if pdf_text is None:
        pdf_text = ""

    # combine all possible text sources
    if item.get("desc"):
        text += " " + item["desc"]

    if item.get("attchmntText"):
        text += " " + item["attchmntText"]

    if item.get("attchmntFile"):
        text += " " + item["attchmntFile"]

    if pdf_text:
        pdf_text = pdf_text[:1500]  # hedge-fund context window
        text += " " + pdf_text

    # normalize text
    text = text.lower()
    text = text.replace("\n", " ")

    # remove ordinal noise
    text = text.replace("1st", "1")
    text = text.replace("2nd", "2")
    text = text.replace("3rd", "3")
    text = text.replace("4th", "4")

    print("QUARTER DETECTION INPUT:", text[:300])



    # ---------- PRIORITY 0: FY RANGE DETECTION (FY25-26 style) ----------

    fy_range_match = re.search(
        r"(q[1-4])[^a-z0-9]{0,10}fy\s*(\d{2})\s*-\s*(\d{2})",
        text
    )

    if fy_range_match:

        q = fy_range_match.group(1).upper()

        start = int(fy_range_match.group(2))
        end = int(fy_range_match.group(3))

        fy = 2000 + end

        print("FY RANGE DETECTED:", q, fy)

        return f"FY{fy}_{q}"

    # ---------- PRIORITY 1: PERIOD ENDED DETECTION ----------

    period_match = re.search(
        r"(march|june|september|december)\s*(\d{1,2})?[, ]*(20\d{2})",
        text
    )

    if period_match and ("quarter" in text or "period" in text):

        month = period_match.group(1)
        year = int(period_match.group(3))

        # Financial year mapping
        if month == "march":
            fy = year
            q = "Q4"

        elif month == "june":
            fy = year + 1
            q = "Q1"

        elif month == "september":
            fy = year + 1
            q = "Q2"

        elif month == "december":
            fy = year + 1
            q = "Q3"

        print("PERIOD ENDED DETECTED:", month, year)

        return f"FY{fy}_{q}"
    
    # -------- STRONG QUARTER DETECTOR (NEW) --------

    quarter_phrase = re.search(
        r"(first|second|third|fourth)\s+quarter.*?fy\s*(20\d{2})",
        text
    )

    if quarter_phrase:

        q_map = {
            "first": "Q1",
            "second": "Q2",
            "third": "Q3",
            "fourth": "Q4"
        }

        q = q_map[quarter_phrase.group(1)]
        fy = quarter_phrase.group(2)

        print("QUARTER PHRASE DETECTED:", q, fy)

        return f"FY{fy}_{q}"

    # ---------- PRIORITY 2: QUARTER PHRASE DETECTION ----------

    quarter_phrase = re.search(
        r"(first|second|third|fourth|1st|2nd|3rd|4th|q1|q2|q3|q4)[^\n]{0,40}?(fy|fiscal)[^\d]{0,10}(20\d{2}|\d{2})",
        text
    )

    if quarter_phrase:

        q_raw = quarter_phrase.group(1)
        fy_raw = quarter_phrase.group(3)

        # normalize quarter
        q_map = {
            "first": "Q1",
            "1st": "Q1",
            "q1": "Q1",
            "second": "Q2",
            "2nd": "Q2",
            "q2": "Q2",
            "third": "Q3",
            "3rd": "Q3",
            "q3": "Q3",
            "fourth": "Q4",
            "4th": "Q4",
            "q4": "Q4"
        }

        q = q_map.get(q_raw.lower(), None)

        if not q:
            return None

        # normalize FY
        if len(fy_raw) == 2:
            fy = "20" + fy_raw
        else:
            fy = fy_raw

        print("QUARTER PHRASE DETECTED:", q, fy)

        return f"FY{fy}_{q}"


    

    # safety fallback
    if "ended december" not in text and "ended september" not in text:
        if item.get("desc"):
            text += " " + item["desc"]

    text = text.lower()

    # -------- TEXT NORMALIZATION (NEW FIX) --------
    text = text.replace("\n", " ")
    text = text.replace("st", "")
    text = text.replace("nd", "")
    text = text.replace("rd", "")
    text = text.replace("th", "")

    print("NORMALIZED TEXT SAMPLE:", text[:300])

    # ---------------- STEP 0: Detect Q3 FY26 style ----------------

    fy_match = re.search(r"q([1-4])\s*fy\s*(\d{2,4})", text)

    if fy_match:
        q = fy_match.group(1)
        fy = fy_match.group(2)

        if len(fy) == 2:
            fy = "20" + fy

        return f"FY{fy}_Q{q}"
    
    quarter_word_match = re.search(
        r"(first|second|third|fourth)\s+quarter.*?(fy\s*\d{2,4}|20\d{2})",
        text
    )

    if quarter_word_match:

        q_map = {
            "first": "Q1",
            "second": "Q2",
            "third": "Q3",
            "fourth": "Q4"
        }

        q = q_map[quarter_word_match.group(1)]

        fy_text = quarter_word_match.group(2)

        fy = re.search(r"\d{2,4}", fy_text).group()

        if len(fy) == 2:
            fy = "20" + fy

        return f"FY{fy}_{q}"

    # ---------------- STEP 1: Detect month + year (FIXED REGEX) ----------------

    date_match = re.search(
        r"(march|june|september|december)\s+\d{1,2}[^0-9]{0,5}(20\d{2})",
        text
    )

    if date_match:

        month = date_match.group(1)
        year = date_match.group(2)

        year = int(year)

        if month == "march":
            fy = year
        else:
            fy = year + 1

        if month == "march":
            return f"FY{fy}_Q4"

        if month == "june":
            return f"FY{fy}_Q1"

        if month == "september":
            return f"FY{fy}_Q2"

        if month == "december":
            return f"FY{fy}_Q3"

    # ---------------- STEP 2: Explicit patterns ----------------

    patterns = [
        r"q([1-4])\s*fy\s*(\d{2,4})",
        r"fy\s*(\d{2,4})\s*q([1-4])",
        r"([1-4])(st|nd|rd|th)?\s*quarter\s*fy\s*(\d{2,4})"
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:

            nums = [x for x in match.groups() if x and x.isdigit()]

            if len(nums) == 2:

                if int(nums[0]) <= 4:
                    q = nums[0]
                    fy = nums[1]
                else:
                    fy = nums[0]
                    q = nums[1]

                if len(fy) == 2:
                    fy = "20" + fy

                return f"FY{fy}_Q{q}"




    # ---------- PRIORITY 3: ANNOUNCEMENT WINDOW INFERENCE ----------

    try:

        dt = datetime.strptime(item["an_dt"], "%d-%b-%Y %H:%M:%S")
        m = dt.month
        y = dt.year

        # NSE reporting cycles
        fy = y if m <= 3 else y + 1
        # Q1 results season (July–August)
        if m in [7, 8]:
            print("WINDOW INFERENCE: Q1 season")
            return f"FY{fy}_Q1"

        # Q2 results season (Oct–Nov)
        if m in [10, 11]:
            print("WINDOW INFERENCE: Q2 season")
            return f"FY{fy}_Q2"

        # Q3 results season (Jan–Feb)
        if m in [1, 2]:
            print("WINDOW INFERENCE: Q3 season")
            return f"FY{fy}_Q3"

        # Q4 results season (Apr–May)
        if m in [4, 5]:
            print("WINDOW INFERENCE: Q4 season")
            return f"FY{fy}_Q4"

    except:
        pass
    # ---------------- STEP 3: Fallback to announcement date ----------------

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


def extract_year(item):

    from datetime import datetime
    import re

    text = ""

    if item.get("desc"):
        text += item["desc"]

    if item.get("attchmntText"):
        text += " " + item["attchmntText"]

    match = re.search(r"20\d{2}", text)

    if match:
        return match.group()

    try:
        dt = datetime.strptime(item["an_dt"], "%d-%b-%Y %H:%M:%S")
        return str(dt.year)
    except:
        return "2025"


# ---------------- ANNOUNCEMENT CHECK ----------------

def check_announcements(symbol, start_date=None, end_date=None):

    announcements = get_announcements(symbol)

    if not announcements:
        return [], 0, 0, 0

    total_announcements = len(announcements)

    if start_date or end_date:
        announcements = filter_by_date_range(announcements, start_date, end_date)

    filtered_count = len(announcements)

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

        size_text = item.get("attFileSize") or item.get("fileSize")

        if size_text:
            try:
                size_value = float(size_text.split()[0])
                if size_value < 80:
                    continue
            except:
                pass

        url = item["attchmntFile"]

        if not url.startswith("http"):
            url = "https://nsearchives.nseindia.com/" + url

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

        unique_key = f"{symbol}_{category}_{item.get('an_dt','')}"

        if unique_key in downloaded_keys:
            continue

        downloaded_keys.add(unique_key)

        filename = url.split("/")[-1]

        if filename in downloaded_files:
            continue

        downloaded_files.add(filename)

        temp_folder = base_folder / "temp"
        temp_folder.mkdir(parents=True, exist_ok=True)

        try:

            success = download_file(url, temp_folder)
            print("DOWNLOAD STATUS:", success)

            if success:

                pdf_path = temp_folder / filename

                pdf_text = extract_pdf_text_first_page(pdf_path)

                print("PDF TEXT SAMPLE:", pdf_text[:200])

                correct_period = detect_quarter(item, pdf_text)

                print("DETECTED PERIOD:", correct_period)

                final_folder = base_folder / correct_period / category
                final_folder.mkdir(parents=True, exist_ok=True)

                final_path = final_folder / filename

                pdf_path.rename(final_path)

                corrected_category = validate_with_pdf(final_path, category)

                if corrected_category != category:

                    new_folder = base_folder / correct_period / corrected_category
                    new_folder.mkdir(parents=True, exist_ok=True)

                    final_path.rename(new_folder / filename)

                try:
                    if pdf_path.exists():
                        pdf_path.unlink()
                except:
                    pass

                count += 1

        except Exception as e:
            print("DOWNLOAD ERROR:", e)

        time.sleep(1)

    return count