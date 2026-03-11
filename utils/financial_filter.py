def is_financial_announcement(item):

    keywords = [

        # results
        "financial results",
        "quarterly results",
        "annual results",
        "unaudited results",
        "audited results",

        # investor
        "investor presentation",
        "analyst meet",
        "investor call",

        # concall
        "conference call",
        "earnings call",
        "concall",
        "transcript",

        # reports
        "annual report",
        "financial report",
        "board meeting outcome",
        "outcome of board meeting"
    ]

    text = ""

    if item.get("desc"):
        text += item["desc"].lower()

    if item.get("attchmntText"):
        text += " " + item["attchmntText"].lower()

    for keyword in keywords:

        if keyword in text:
            return True

    return False