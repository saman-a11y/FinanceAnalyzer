def is_financial_announcement(item, pdf_text=None):

    keywords = [

        # quarterly results
        "financial results",
        "quarterly results",
        "results for the quarter",
        "quarter ended",
        "unaudited financial results",
        "audited financial results",
        "limited review report",

        # board meeting approvals
        "board meeting outcome",
        "outcome of board meeting",
        "outcome of the board meeting",

        # investor communication
        "investor presentation",
        "corporate presentation",
        "earnings presentation",
        "analyst meet",
        "analyst call",
        "investor call",
        "investor meet",

        # concall transcripts
        "conference call",
        "earnings call",
        "concall",
        "call transcript",
        "conference call transcript",
        "earnings call transcript",
        "transcript",

        # annual reports
        "annual report",
        "integrated annual report",
        "financial report",
        "annual financial statements",

        # regulation filings (very common)
        "regulation 33",
        "regulation 30"
    ]

    text = ""

    if item.get("desc"):
        text += item["desc"].lower()

    if item.get("attchmntText"):
        text += " " + item["attchmntText"].lower()

    if item.get("attchmntFile"):
        text += " " + item["attchmntFile"].lower()

    # 🔥 ADD THIS (PDF intelligence)
    if pdf_text:
        text += " " + pdf_text[:3000].lower()   # increased context

    # ---------------- STEP 1: BASIC MATCH ----------------
    base_match = any(k in text for k in keywords)

    if not base_match:
        return False

    # ---------------- STEP 2: REMOVE NOISE ----------------
    if is_noise_document(text):
        return False

    # ---------------- STEP 3: MUST HAVE FINANCIAL DATA ----------------
    if not has_financial_data(text):
        return False

    return True


# ---------------- FINANCIAL DATA CHECK ----------------
def has_financial_data(text):

    text = text.lower()

    strong_keywords = [
        "revenue",
        "total income",
        "net profit",
        "profit after tax",
        "ebitda",
        "expenses",
        "assets",
        "liabilities",
        "cash flow"
    ]

    # keyword scoring
    score = sum(1 for k in strong_keywords if k in text)

    # 🔥 NEW: number pattern detection (VERY IMPORTANT)
    import re
    number_hits = len(re.findall(r"\d+\.?\d*\s*(crore|cr|million|lakh|₹|rs)", text))

    # 🔥 FINAL DECISION (stronger logic)
    if score >= 3 and number_hits >= 2:
        return True

    return False


# ---------------- NOISE DETECTION ----------------
def is_noise_document(text):

    text = text.lower()

    noise_keywords = [
        "conference call",
        "transcript",
        "investor meet",
        "earnings call",
        "audio recording",
        "board meeting",
        "newspaper publication",
        "press release"
    ]

    # 🔥 STRICTER FILTER (avoid false positives)
    count = sum(1 for k in noise_keywords if k in text)

    return count >= 2


def has_financial_table_structure(text):

    text = text.lower()

    table_indicators = [
        "particulars",
        "income",
        "expenses",
        "profit before tax",
        "profit after tax",
        "total income",
        "segment revenue",
        "standalone",
        "consolidated"
    ]

    count = sum(1 for k in table_indicators if k in text)

    return count >= 3