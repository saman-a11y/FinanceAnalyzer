def classify_announcement(item):

    text = ""

    fields = [
        "desc",
        "attchmntText",
        "attchmntFile",
        "sm_name",
        "sm_category"
    ]

    for field in fields:

        if field in item and item[field]:

            text += " " + str(item[field]).lower()


    # Quarterly results
    if "quarter" in text or "q1" in text or "q2" in text or "q3" in text or "q4" in text:
        return "quarterly_results"


    # Annual results
    if "annual result" in text or "financial year" in text or "fy" in text:
        return "annual_results"


    # Investor presentations
    if "investor presentation" in text or "presentation" in text:
        return "investor_presentations"


    # Earnings calls
    if "concall" in text or "conference call" in text or "earnings call" in text:
        return "concalls"


    # Transcripts
    if "transcript" in text:
        return "transcripts"


    return "other_financial"