import pdfplumber

def preview_pdf(pdf_path):

    text = ""

    try:

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages[:2]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

    except:
        return "Preview unavailable"

    return text[:1500]