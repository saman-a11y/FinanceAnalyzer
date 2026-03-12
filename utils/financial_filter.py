def is_financial_announcement(item):

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

    for keyword in keywords:

        if keyword in text:
            return True

    return False