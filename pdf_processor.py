def process_pdf(original_path: str, output_dir: str):
    """
    PDF'den belirli metinleri siler ve 'Full Name' değerine göre adlandırır.
    Sonucu dict olarak döner (API için uygun).
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        temp_pdf = os.path.join(output_dir, "temp_cleaned.pdf")

        # Full name çıkarma (hata olursa None döner)
        try:
            full_name = extract_full_name(original_path)
        except Exception as e:
            print(f"⚠ Full name çıkarılamadı: {e}")
            full_name = None

        # PDF temizleme (hata olursa orijinali kopyala)
        try:
            remove_text_from_pdf(original_path, temp_pdf)
        except Exception as e:
            print(f"⚠ PDF temizleme hatası, orijinal kullanılacak: {e}")
            import shutil
            shutil.copy(original_path, temp_pdf)

        # Dosyayı adlandır
        if full_name:
            sanitized_full_name = sanitize_filename(full_name)
            new_filename = f"{sanitized_full_name}.pdf"
        else:
            # Full name yoksa UUID ile adlandır
            from uuid import uuid4
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
        print(f"❌ PDF işleme hatası: {e}")
        # En kötü durumda orijinal dosyayı döndür
        import shutil
        from uuid import uuid4
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
