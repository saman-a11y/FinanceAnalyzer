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

    # 1️⃣ Transcript / Concall
    transcript_keywords = [
        "transcript",
        "concall",
        "conference call",
        "earnings call",
        "analyst meet transcript",
        "investor call transcript"
    ]

    if any(k in text for k in transcript_keywords):
        return "quarterly_transcripts"


    # 2️⃣ Investor presentation
    presentation_keywords = [
        "investor presentation",
        "presentation",
        "analyst presentation",
        "earnings presentation",
        "investor deck"
    ]

    if any(k in text for k in presentation_keywords):
        return "investor_presentations"


    # 3️⃣ Annual report
    annual_keywords = [
        "annual report",
        "annual financial results",
        "financial year",
        "fy results",
        "audited financial results",
        "audited results"
    ]

    if any(k in text for k in annual_keywords):
        return "annual_reports"


    # 4️⃣ Quarterly results
    quarterly_keywords = [
        "quarterly results",
        "financial results",
        "results for the quarter",
        "q1 results",
        "q2 results",
        "q3 results",
        "q4 results",
        "board meeting outcome",
        "outcome of the board meeting",
        "unaudited financial results"
    ]

    if any(k in text for k in quarterly_keywords):
        return "quarterly_results"


    # fallback
    return "other_financial"