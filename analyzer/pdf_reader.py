import pdfplumber

def extract_text_from_pdf(file_path):

    text = ""

    try:
        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text

    except Exception as e:
        print("Error reading PDF:", e)

    return text