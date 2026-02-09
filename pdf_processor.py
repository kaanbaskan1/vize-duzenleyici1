import os
import re
import pdfplumber
import pdf_redactor
import logging

logger = logging.getLogger(__name__)

def extract_full_name(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    match = re.search(r"Full Name\s*:\s*(.+)", text)
                    if match:
                        return match.group(1).strip()
    except Exception as e:
        logger.error(f"Error extracting full name: {e}")
    return None

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜ\s]', '', filename).strip()

def process_pdf(input_path, output_path):
    options = pdf_redactor.RedactorOptions()
    options.content_filters = [
        (re.compile(r"TEL:\s*\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*\d+[,/.\s\d]*"), lambda m: ""),
        (re.compile(r"M\s*B\s*D\s*TOURISM\s*L\.?L\.?C\.?", re.IGNORECASE), lambda m: ""),
        (re.compile(r"HAIR\s*OF\s*ISTANBUL\s*TOURISM\s*L\.?L\.?C\.?", re.IGNORECASE), lambda m: ""),
        (re.compile(r"HAIR\s*OF\s*ISTANBUL", re.IGNORECASE), lambda m: ""),
        (re.compile(r"TOURISM\s*L\.?L\.?C\.?", re.IGNORECASE), lambda m: ""),
        (re.compile(r"Tel\s*(?:no)?:?\s*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r",?\s*Mob[:\s]*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r"Arkan\s*Tourism\s*LLC", re.IGNORECASE), lambda m: ""),
        (re.compile(r"\bArkan\b", re.IGNORECASE), lambda m: ""),
        (re.compile(r",?\s*Mob\s*\+971\s*54\s*560\s*4204"), lambda m: ""),
        (re.compile(r"\u0645\.\u0645\.\u0630\.\u0634\s*\u0629\u062d\u0627\u064a\u0633\u0644\u0644\s*\u064a\u062f\s*\u064a\u0628\s*\u0645\u0627"), lambda m: ""),
        (re.compile(r"\u0645\.\u0645\.\u0630\s*\u0629\u062d\u0627\u064a\u0633\u0644\u0644\s*\u0646\u0627\u0643\u0631\u0623"), lambda m: ""),
    ]

    with open(input_path, "rb") as inp:
        options.input_stream = inp
        with open(output_path, "wb") as out:
            options.output_stream = out
            pdf_redactor.redactor(options)

    full_name = extract_full_name(output_path)
    return output_path, full_name
