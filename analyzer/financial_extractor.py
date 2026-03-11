import re
import pdfplumber


def extract_financial_summary(pdf_path):

    summary = {
        "Revenue": None,
        "Profit": None,
        "EPS": None
    }

    try:

        with pdfplumber.open(pdf_path) as pdf:

            text = ""

            for page in pdf.pages[:3]:

                t = page.extract_text()

                if t:
                    text += t.lower()

        # Revenue
        rev_match = re.search(r"(revenue|total income)[^\d]*(\d[\d,\.]*)", text)

        if rev_match:
            summary["Revenue"] = rev_match.group(2)

        # Profit
        profit_match = re.search(r"(net profit|profit after tax)[^\d]*(\d[\d,\.]*)", text)

        if profit_match:
            summary["Profit"] = profit_match.group(2)

        # EPS
        eps_match = re.search(r"(eps|earnings per share)[^\d]*(\d[\d,\.]*)", text)

        if eps_match:
            summary["EPS"] = eps_match.group(2)

    except:
        pass

    return summary



def generate_ai_summary(summary):

    insights = []

    if summary.get("Revenue"):
        insights.append(f"Revenue reported: {summary['Revenue']}")

    if summary.get("Profit"):
        insights.append(f"Net profit reported: {summary['Profit']}")

    if summary.get("EPS"):
        insights.append(f"Earnings per share: {summary['EPS']}")

    if len(insights) == 0:
        insights.append("Financial numbers could not be extracted automatically.")

    return insights