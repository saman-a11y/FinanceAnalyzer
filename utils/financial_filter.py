def is_financial_announcement(item):

    keywords = [
        "result",
        "financial",
        "quarter",
        "annual",
        "earnings",
        "investor presentation",
        "presentation",
        "concall",
        "earnings call",
        "transcript",
        "analyst meet",
        "conference call",
        "board meeting",
        "financial results",
        "auditor",
        "balance sheet"
    ]

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

    for keyword in keywords:

        if keyword in text:

            return True

    return False