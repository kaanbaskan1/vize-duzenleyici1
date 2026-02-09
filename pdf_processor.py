# -*- coding: utf-8 -*-
import os
import re
import shutil
from uuid import uuid4

import pdfplumber
import pdf_redactor


def extract_full_name(pdf_path: str):
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
    return re.sub(r'[^a-zA-Z\s]', '', filename).strip()


def remove_text_from_pdf(input_pdf: str, output_pdf: str):
    options = pdf_redactor.RedactorOptions()

    options.content_filters = [
        # MBD / Arkan - English
        (re.compile(r"TEL:\s*\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*\d+[,/.\s\d]*"), lambda m: ""),
        (re.compile(r"M B D TOURISM L\.L\.C"), lambda m: ""),
        (re.compile(r"Tel\s*(?:no)?:?\s*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r",?\s*Mob[:\s]*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r"Arkan\s*Tourism\s*LLC", re.IGNORECASE), lambda m: ""),
        # Hair of Istanbul - English only (Arapca 
