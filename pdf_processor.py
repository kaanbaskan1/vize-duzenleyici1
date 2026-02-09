# -*- coding: utf-8 -*-
import os
import re
import shutil
from uuid import uuid4

import pdfplumber
import pikepdf


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
    pdf = pikepdf.open(input_pdf)

    # Sadece ASCII pattern'ler - Arapca hex glyph'lere dokunmaz
    patterns = [
        # Hair of Istanbul - tam string
        rb"\(HAIR OF ISTANBUL  TOURISM L\.L\.C\)",
        rb"\(HAIR OF ISTANBUL TOURISM L\.L\.C\)",
        rb"\(HAIR OF ISTANBUL  TORUISM L\.L\.C\)",
        rb"\(HAIR OF ISTANBUL TORUISM L\.L\.C\)",
        # Hair of Istanbul - parcali TJ array icinde
        rb"HAIR OF ISTANBUL",
        # MBD
        rb"M B D TOURISM L\.L\.C",
        # Arkan
        rb"Arkan Tourism LLC",
        rb"Arkan\s*Tourism\s*LLC",
    ]

    # Telefon ve adres - bunlar kesinlikle ASCII
    contact_patterns = [
        rb"TEL:\s*042[56]\d+",
        rb"TEL:\s*\d{6,}",
        rb"P\.O\.BOX:\s*1\s*,\s*2/1/482537",
        rb"P\.O\.BOX:\s*\d+[,/.\s\d]*",
        rb"Tel\s*no\s*:\s*\+?\d[\d\s\-]+",
        rb"Mob\s*:\s*\+?\d[\d\s\-]+",
    ]

    for page in pdf.pages:
        content_obj = page.get("/Contents")
        if content_obj is None:
            continue

        if isinstance(content_obj, pikepdf.Array):
            streams = list(content_obj)
        else:
            streams = [content_obj]

        for stream_ref in streams:
            try:
                raw = stream_ref.read_bytes()
                modified = raw

                for pat in patterns:
                    # Sadece ASCII byte'lari etkiler
                    modified = re.sub(pat, b"", modified)

                for pat in contact_patterns:
                    modified = re.sub(pat, b"", modified)

                if modified != raw:
                    stream_ref.write(modified)
            except Exception as e:
                print(f"Stream isleme hatasi: {e}")
                continue

    pdf.save(output_pdf)
    pdf.close()


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
