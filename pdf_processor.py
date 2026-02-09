# -*- coding: utf-8 -*-
import os
import re
import shutil
from uuid import uuid4

import pdfplumber
import pdf_redactor


def extract_full_name(pdf_path: str):
    """
    PDF'den 'Full Name :' ve 'Full Name:' bilgisini çıkarır.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    match = re.search(r"Full Name\s*:\s*(.+)", text)
                    if match:
                        return match.group(1).strip()
    except Exception as e:
        print(f"Full name cikarma hatasi: {e}")
    return None


def sanitize_filename(filename: str):
    return re.sub(r'[^a-zA-ZcCgGiIoOsSuU\s]', '', filename).strip()


def remove_text_from_pdf(input_pdf: str, output_pdf: str):
    options = pdf_redactor.RedactorOptions()
    options.content_filters = [
        (re.compile(r"TEL:\s*\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*\d+[,/.\s\d]*"), lambda m: ""),
        (re.compile(r"M B D TOURISM L\.L\.C"), lambda m: ""),
        (re.compile(r"\uFEE1\.\uFEE1\.\uFEAB\.\uFEB5\s*\uFEA4\uFE8E\uFEF4\uFEB4\uFEE0\uFEDF\s*\uFEF1\uFEA9\s*\uFEF2\uFE91\s*\uFEE1\uFE8D"), lambda m: ""),
        (re.compile(r"\u0645\.\u0645\.\u0630\s*\uFEA4\uFE8E\uFEF3\uFEB4\uFEE0\uFEDF\s*\u0646\uFE8E\uFEDB\u0631\u0623"), lambda m: ""),
        (re.compile(r"\u0645\.\u0645\.\u0630\s*\u0629\u062D\u0627\u064A\u0633\u0644\u0644\s*\u0646\u0627\u0643\u0631\u0623"), lambda m: ""),
        (re.compile(r"Tel\s*(?:no)?:?\s*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r",?\s*Mob[:\s]*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r"Arkan\s*Tourism\s*LLC", re.IGNORECASE), lambda m: ""),
        (re.compile(r",?\s*Mob\s*\+971\s*54\s*560\s*4204"), lambda m: ""),
        (re.compile(r"HAIR OF ISTANBUL TORUISM L\.L\.C", re.IGNORECASE), lambda m: ""),
        (re.compile(r"HAIR OF ISTANBUL TOURISM L\.L\.C", re.IGNORECASE), lambda m: ""),
        (re.compile(r"HAIR\s*OF\s*ISTANBUL\s*TOUR?UISM\s*L\.?L\.?C", re.IGNORECASE), lambda m: ""),
        (re.compile(r"TEL:\s*042659878"), lambda m: ""),
        (re.compile(r"TEL:\s*042549878"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*1\s*,\s*2/1/482537"), lambda m: ""),
        (re.compile(r"\u0647\u064A\u0631\s*\u0627\u0648\u0641\s*\u0627\u0633\u0637\u0646\u0628\u0648\u0644\s*\u0644\u0644\u0633\u06
