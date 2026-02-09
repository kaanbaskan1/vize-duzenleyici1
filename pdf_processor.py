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

    patterns = [
        # Hair of Istanbul - tum varyantlar
        rb"HAIR\s+OF\s+ISTANBUL\s+TOUR[UI]ISM\s+L\.?L\.?C",
        rb"HAIR\s+OF\s+ISTANBUL",
        # Arkan
        rb"Arkan\s*Tourism\s*LLC",
        # MBD
        rb"M\s*B\s*D\s*TOURISM\s*L\.?L\.?C",
        # Telefon numaralari - tum formatlar
        rb"Tel:\+[\d\-]+",
        rb"TEL:\s*\d+",
        rb",?\s*Mob:\s*\+?[\d\-]+",
        # PO Box
        rb"P\.?O\.?BOX:?\s*[\d,/.\s]+",
    ]

    for page in pdf.pages:
        if "/Contents" not in page:
            continue
        contents = page["/Contents"]
        if isinstance(contents, pikepdf.Array):
            streams = list(contents)
        else:
            streams = [contents]
        new_streams = []
        for stream_ref in streams:
            stream = stream_ref.resolve() if hasattr(stream_ref, 'resolve') else stream_ref
            try:
                raw = stream.read_bytes()
            except Exception:
                new_streams.append(stream_ref)
                continue
            modified = raw
            for pattern in patterns:
                modified = re.sub(pattern, b"", modified)
            if modified != raw:
                stream.write(modified)
            new_streams.append(stream_ref)

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
