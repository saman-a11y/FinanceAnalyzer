import requests
import zipfile
import io
from utils.announcement_classifier import classify_announcement


def create_zip(symbol, reports):

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

        for report in reports:

            url = report.get("attchmntFile")

            if not url:
                continue

            try:

                headers = {"User-Agent": "Mozilla/5.0"}

                response = requests.get(url, headers=headers, timeout=20)

                if response.status_code != 200:
                    continue

                category = classify_announcement(report)

                filename = url.split("/")[-1]

                path = f"{symbol}/{category}/{filename}"

                zip_file.writestr(path, response.content)

            except:
                continue

    zip_buffer.seek(0)

    return zip_buffer