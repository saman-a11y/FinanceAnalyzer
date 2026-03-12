import fitz

def extract_pdf_text_first_page(pdf_path):

    try:

        doc = fitz.open(pdf_path)

        text = ""

        pages_to_read = min(5, len(doc))

        for i in range(pages_to_read):

            page = doc.load_page(i)

            text += page.get_text("text")

            blocks = page.get_text("blocks")

            for b in blocks:
                text += " " + b[4]

        doc.close()

        text = text.lower()

        text = text.replace("\n", " ")

        return text

    except Exception as e:

        print("PDF TEXT READ ERROR:", e)

        return ""