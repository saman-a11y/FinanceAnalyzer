from datetime import datetime
from pipeline.download_pipeline import run_download_pipeline
from utils.auth import authenticate_user

# Password check
if not authenticate_user():
    exit()

symbol = input("Enter company symbol: ").upper()

start = input("Start date (YYYY-MM-DD) or press Enter: ")
end = input("End date (YYYY-MM-DD) or press Enter: ")

start_date = datetime.fromisoformat(start) if start else None
end_date = datetime.fromisoformat(end) if end else None

run_download_pipeline(symbol, start_date, end_date)