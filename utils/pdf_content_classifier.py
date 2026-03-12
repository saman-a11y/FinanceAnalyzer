import pdfplumber


def validate_with_pdf(pdf_path, predicted_category):

    try:

        text = ""

        with pdfplumber.open(pdf_path) as pdf:

            pages_to_check = min(2, len(pdf.pages))

            for i in range(pages_to_check):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text += page_text.lower()

    except:
        return predicted_category


    # ---------- Transcript detection ----------

    transcript_markers = [

        "operator:",
        "analyst:",
        "question:",
        "answer:",

        "conference call transcript",
        "earnings call transcript",
        "earnings call",
        "conference call",
        "concall transcript",
        "concall",

        "investor call transcript",
        "analyst call transcript",

        "earnings discussion",
        "earnings discussion transcript"
    ]

    if any(k in text for k in transcript_markers):
        return "quarterly_transcripts"


    # ---------- Investor presentation ----------

    presentation_markers = [
        "investor presentation",
        "corporate presentation",
        "growth strategy",
        "company overview"
    ]

    if any(k in text for k in presentation_markers):
        return "investor_presentations"


    # ---------- Annual report ----------

    annual_markers = [
        "balance sheet",
        "director's report",
        "auditor's report",
        "statement of profit and loss"
    ]

    if any(k in text for k in annual_markers):
        return "annual_reports"


    # ---------- Quarterly results ----------

    results_markers = [
        "financial results for the quarter",
        "standalone financial results",
        "consolidated financial results"
    ]

    if any(k in text for k in results_markers):
        return "quarterly_results"


    return predicted_category