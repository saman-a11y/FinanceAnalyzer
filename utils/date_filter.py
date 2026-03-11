from datetime import datetime

def filter_by_date_range(announcements, start_date=None, end_date=None):

    filtered = []

    for item in announcements:

        date_str = item.get("sort_date")

        if not date_str:
            continue

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        except:
            continue

        start = start_date.date() if start_date else None
        end = end_date.date() if end_date else None

        if start and date < start:
            continue

        if end and date > end:
            continue

        filtered.append(item)

    return filtered