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
        (re.compile(r"TEL:\s*\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*\d+[,/.\s\d]*"), lambda m: ""),
        (re.compile(r"M B D TOURISM L\.L\.C"), lambda m: ""),
        (re.compile(r"Tel\s*(?:no)?:?\s*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r",?\s*Mob[:\s]*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r"Arkan\s*Tourism\s*LLC", re.IGNORECASE), lambda m: ""),
        (re.compile(r"HAIR\s*OF\s*ISTANBUL\s*TOUR?[UI]ISM\s*L\.?L\.?C", re.IGNORECASE), lambda m: ""),
        (re.compile(r"TEL:\s*042[56]\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*1\s*,\s*2/1/482537"), lambda m: ""),
    ]

    options.input_stream = input_pdf
    options.output_stream = output_pdf
    pdf_redactor.redactor(options)


def process_pdf(original_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        temp_pdf = os.path.join(output_dir, "temp_cleaned.pdf")
        full_name = extract_full_name(original_path)
        try:
            remove_text_from_pdf(original_path, temp_pdf)
        except Exception as e:
            print(f"PDF temizleme hatasi: {e}")
            shutil.copy(original_path, temp_pdf)
        if full_name:
            sanitized = sanitize_filename(full_name)
            new_filename = f"{sanitized}.pdf"
        else:
            new_filename = f"vize_{uuid4().hex[:8]}.pdf"
        new_path = os.path.join(output_dir, new_filename)
        os.replace(temp_pdf, new_path)
        return {
            "success": full_name is not None,
            "full_name": full_name,
            "filename": new_filename,
            "output_path": new_path,
        }
    except Exception as e:
        print(f"PDF isleme hatasi: {e}")
        try:
            fallback_name = f"fallback_{uuid4().hex[:8]}.pdf"
            fallback_path = os.path.join(output_dir, fallback_name)
            shutil.copy(original_path, fallback_path)
            return {
                "success": False,
                "full_name": None,
                "filename": fallback_name,
                "output_path": fallback_path,
                "error": str(e),
            }
        except Exception as fe:
            return {
                "success": False,
                "full_name": None,
                "filename": None,
                "output_path": None,
                "error": str(fe),
            }
