import re


def normalize(text):

    if not text:
        return ""

    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text


def classify_announcement(item):

    text = ""

    if item.get("desc"):
        text += " " + item["desc"]

    if item.get("attchmntText"):
        text += " " + item["attchmntText"]

    if item.get("attchmntFile"):
        text += " " + item["attchmntFile"]

    text = normalize(text)

    # ---------------- PRIORITY RULES ----------------

    # 1️⃣ Transcript / Concall (highest priority)

    transcript_keywords = [
        "transcript",
        "conference call transcript",
        "earnings call transcript",
        "analyst call transcript",
        "investor call transcript",
        "conference call",
        "earnings call",
        "concall",
        "analyst meet call"
    ]

    if any(k in text for k in transcript_keywords):
        return "quarterly_transcripts"

    # 2️⃣ Investor presentations

    presentation_keywords = [
        "investor presentation",
        "corporate presentation",
        "earnings presentation",
        "results presentation",
        "analyst presentation",
        "investor deck",
        "company presentation",
        "investor update",
        "analyst meet presentation"
    ]

    if any(k in text for k in presentation_keywords):
        return "investor_presentations"

    # 3️⃣ Annual reports

    annual_keywords = [
        "annual report",
        "integrated annual report",
        "annual financial statements",
        "financial year",
        "fy results",
        "audited financial results",
        "audited results",
        "regulation 34"
    ]

    if any(k in text for k in annual_keywords):
        return "annual_reports"

    # 4️⃣ Quarterly results

    quarterly_keywords = [
        "quarterly results",
        "financial results",
        "results for the quarter",
        "quarter ended",
        "q1 results",
        "q2 results",
        "q3 results",
        "q4 results",
        "unaudited financial results",
        "limited review report",
        "regulation 33"
    ]

    if any(k in text for k in quarterly_keywords):
        return "quarterly_results"

    # 5️⃣ Board meeting outcomes (only if financial)

    board_keywords = [
        "outcome of board meeting",
        "outcome of the board meeting",
        "board meeting outcome"
    ]

    if any(k in text for k in board_keywords):

        if "result" in text or "financial" in text:
            return "quarterly_results"

        return "other_financial"

    # 6️⃣ Ignore newspaper publication

    newspaper_keywords = [
        "newspaper publication",
        "copy of newspaper",
        "advertisement"
    ]

    if any(k in text for k in newspaper_keywords):
        return "other_financial"

    return "other_financial"