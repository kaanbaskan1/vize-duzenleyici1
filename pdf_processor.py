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
        print(f"⚠ Full name çıkarma hatası: {e}")
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
    try:
        os.makedirs(output_dir, exist_ok=True)
        temp_pdf = os.path.join(output_dir, "temp_cleaned.pdf")

        # Full name çıkarma (hata olursa None döner)
        full_name = extract_full_name(original_path)

        # PDF temizleme (hata olursa orijinali kopyala)
        try:
            remove_text_from_pdf(original_path, temp_pdf)
        except Exception as e:
            print(f"⚠ PDF temizleme hatası, orijinal kullanılacak: {e}")
            shutil.copy(original_path, temp_pdf)

        # Dosyayı adlandır
        if full_name:
            sanitized_full_name = sanitize_filename(full_name)
            new_filename = f"{sanitized_full_name}.pdf"
        else:
            # Full name yoksa UUID ile adlandır
            new_filename = f"vize_{uuid4().hex[:8]}.pdf"

        new_path = os.path.join(output_dir, new_filename)
        os.replace(temp_pdf, new_path)

        print(f"✅ Dosya temizlendi ve {new_filename} olarak kaydedildi!")

        return {
            "success": full_name is not None,
            "full_name": full_name,
            "filename": new_filename,
            "output_path": new_path,
        }

    except Exception as e:
        print(f"❌ PDF işleme hatası: {e}")
        # En kötü durumda orijinal dosyayı döndür
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
        except Exception as fallback_error:
            return {
                "success": False,
                "full_name": None,
                "filename": None,
                "output_path": None,
                "error": f"Orijinal hata: {e}, Fallback hata: {fallback_error}",
            }
