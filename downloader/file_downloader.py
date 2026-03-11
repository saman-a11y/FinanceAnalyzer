import requests
from pathlib import Path


def download_file(url, folder):

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-1]
    path = folder / filename

    # Prevent duplicate downloads
    if path.exists():
        print("Already exists:", filename)
        return True

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
        "Referer": "https://www.nseindia.com/",
        "Accept": "application/pdf"
    }

    try:
        response = requests.get(
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