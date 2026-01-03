import os
import re
import pdfplumber
import pdf_redactor


def extract_full_name(pdf_path: str):
    """
    PDF'den 'Full Name :' ve 'Full Name:' bilgisini çıkarır.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                match = re.search(r"Full Name\s*:\s*(.+)", text)
                if match:
                    return match.group(1).strip()
    return None


def sanitize_filename(filename: str):
    """
    Türkçe karakterlere izin verir ve diğer geçersiz karakterleri kaldırır.
    """
    return re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜ\s]', '', filename).strip()


def remove_text_from_pdf(input_pdf: str, output_pdf: str):
    """
    PDF'den belirli metinleri kaldırır.
    """
    options = pdf_redactor.RedactorOptions()
    options.content_filters = [
        (re.compile(r"TEL:\s*\d+"), lambda m: ""),
        (re.compile(r"P\.O\.BOX:\s*\d+[,/.\s\d]*"), lambda m: ""),
        (re.compile(r"M B D TOURISM L\.L\.C"), lambda m: ""),
        (re.compile(r"ﻡ\.ﻡ\.ﺫ\.ﺵ\s*ﺔﺣﺎﻴﺴﻠﻟ\s*ﻱﺩ\s*ﻲﺑ\s*ﻡﺍ"), lambda m: ""),
        (re.compile(r"م\.م\.ذ\s*ﺔﺣﺎﯿﺴﻠﻟ\s*نﺎﻛرأ"), lambda m: ""),
        (re.compile(r"م\.م\.ذ\s*ةحايسلل\s*ناكرأ"), lambda m: ""),
        (re.compile(r"Tel\s*(?:no)?:?\s*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r",?\s*Mob[:\s]*\+?\d{1,3}[-\s]?\d{1,4}[-\s]?\d{4,}"), lambda m: ""),
        (re.compile(r"Arkan\s*Tourism\s*LLC", re.IGNORECASE), lambda m: ""),
        (re.compile(r",?\s*Mob\s*\+971\s*54\s*560\s*4204"), lambda m: ""),
    ]

    options.input_stream = input_pdf
    options.output_stream = output_pdf

    pdf_redactor.redactor(options)


def process_pdf(original_path: str, output_dir: str):
    """
    PDF'den belirli metinleri siler ve 'Full Name' değerine göre adlandırır.
    Sonucu dict olarak döner (API için uygun).
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_pdf = os.path.join(output_dir, "temp_cleaned.pdf")

    full_name = extract_full_name(original_path)

    remove_text_from_pdf(original_path, temp_pdf)

    if full_name:
        sanitized_full_name = sanitize_filename(full_name)
        new_filename = f"{sanitized_full_name}.pdf"
        new_path = os.path.join(output_dir, new_filename)

        os.replace(temp_pdf, new_path)
        print(f"✅ Dosya temizlendi ve {new_filename} olarak kaydedildi!")

        return {
            "success": True,
            "full_name": full_name,
            "filename": new_filename,
            "output_path": new_path,
        }
    else:
        error_dir = os.path.join(output_dir, "Kontrol Ediniz")
        os.makedirs(error_dir, exist_ok=True)

        error_path = os.path.join(error_dir, os.path.basename(original_path))
        os.replace(temp_pdf, error_path)

        print(f"⚠ 'Full Name' bulunamadı. Dosya {error_path} olarak kaydedildi.")

        return {
            "success": False,
            "full_name": None,
            "filename": os.path.basename(error_path),
            "output_path": error_path,
        }
