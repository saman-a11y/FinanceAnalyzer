from utils.financial_filter import has_financial_data, is_noise_document

# ---------------- STRUCTURE CHECK ----------------
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


# ---------------- CLASSIFIER ----------------
def classify_document(text):

    text = text.lower()

    # ❌ HARD EXCLUDE FIRST (VERY IMPORTANT)
    bad_docs = [
        "monitoring agency",
        "newspaper",
        "board meeting",
        "outcome of board meeting",
        "credit rating",
        "trading window",
        "certificate under sebi",
        "regulation 74",
        "regulation 76"
    ]

    if any(k in text for k in bad_docs):
        return "other"

    # ---------- TRANSCRIPT ----------
    if (
        "transcript" in text
        and "management" in text
        and ("question" in text or "answer" in text)
    ):
        return "transcript"

    # ---------- QUARTERLY RESULTS ----------
    if (
        ("financial results" in text or "unaudited financial results" in text)
        and has_financial_table_structure(text)
        and has_financial_data(text)
    ):
        return "quarterly_results"

    return "other"


# ---------------- MAIN PROCESSOR ----------------
def process_document(text):

    text = text.lower()

    doc_type = classify_document(text)

    confidence_score = 0

    # ---------- SCORING SYSTEM ----------

    if "financial results" in text:
        confidence_score += 2

    if "revenue" in text:
        confidence_score += 1

    if "ebitda" in text:
        confidence_score += 1

    if "profit after tax" in text:
        confidence_score += 1

    if "particulars" in text:
        confidence_score += 1

    if "standalone" in text or "consolidated" in text:
        confidence_score += 1

    # transcript signals
    if "conference call" in text and "transcript" in text:
        confidence_score += 2

    # ---------- FINAL CONFIDENCE ----------
    if confidence_score >= 5:
        confidence = "HIGH"
    elif confidence_score >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "type": doc_type,
        "confidence": confidence
    }