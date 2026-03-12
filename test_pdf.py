from utils.pdf_quarter_reader import extract_pdf_text_first_page

pdf = "/Users/samansharma/Downloads/TCS/FY2026_Q4/quarterly_transcripts/TCS_CORPCS_16012026163741_Signed_SEIntimation.pdf"   # put one transcript pdf here

text = extract_pdf_text_first_page(pdf)

print("\nTEXT LENGTH:", len(text))
print("\nFIRST 500 CHARACTERS:\n")
print(text[:500])