import requests
from pathlib import Path

# Persistent session
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Referer": "https://www.nseindia.com/",
    "Accept": "application/pdf",
    "Accept-Language": "en-US,en;q=0.9"
}

# Warm up NSE session properly
try:
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    session.get(
        "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
        headers=headers,
        timeout=10
    )
except:
    pass


def download_file(url, folder):

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-1]
    path = folder / filename

    if path.exists():
        print("Already exists:", filename)
        return True

    try:

        response = session.get(
            url,
            headers=headers,
            stream=True,
            timeout=40
        )

        response.raise_for_status()

        with open(path, "wb") as f:

            for chunk in response.iter_content(chunk_size=8192):

                if chunk:
                    f.write(chunk)

        print("Downloaded:", filename)

        return True

    except Exception as e:

        print("Download failed:", filename)
        print("Error:", e)

        return False
    
from concurrent.futures import ThreadPoolExecutor

def download_files_parallel(urls, headers):

    results = []

    def fetch(url):

        try:
            r = session.get(url, headers=headers, timeout=20)

            if r.status_code == 200:
                return url, r.content

        except:
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = [executor.submit(fetch, u) for u in urls]

        for f in futures:

            res = f.result()

            if res:
                results.append(res)

    return results