# -*- coding: utf-8 -*-
import os
import re
import shutil
from uuid import uuid4

import fitz  # pymupdf
import pdfplumber


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
    doc = fitz.open(input_pdf)

    # Silinecek İngilizce metinler
    search_terms = [
        "HAIR OF ISTANBUL",
        "TOURISM L.L.C",
        "TOURISM LLC",
        "Arkan Tourism LLC",
        "Arkan Tourism",
        "M B D TOURISM L.L.C",
        "M B D TOURISM LLC",
        "MBD TOURISM",
        "P.O.BOX",
        "TEL:",
        "Tel:",
        "Mob:",
    ]

    for page in doc:
        for term in search_terms:
            areas = page.search_for(term)
            for area in areas:
                # Alani biraz genislet (telefon numarasi vs. icin)
                expanded = fitz.Rect(
                    area.x0 - 2,
                    area.y0 - 2,
                    area.x1 + 200,  # Saga dogru genislet (numara, adres vs.)
                    area.y1 + 2
                )
                page.add_redact_annot(expanded, fill=(1, 1, 1))  # Beyaz dolgu
        page.apply_redactions()

    doc.save(output_pdf)
    doc.close()


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
