from analyzer.pdf_reader import extract_text_from_pdf
from analyzer.financial_extractor import extract_financial_data

file_path = "data/TCS/announcements/TCS_CORPCS_09032026123653_PR_09Mar26_signed.pdf"

text = extract_text_from_pdf(file_path)

financial_data = extract_financial_data(text)

print("\nExtracted Financial Data:\n")

for key, value in financial_data.items():
    print(key, ":", value)