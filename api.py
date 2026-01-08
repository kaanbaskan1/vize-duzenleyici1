import base64

@app.post("/process")
async def process_pdf_endpoint(file: UploadFile = File(...)):
    # Sadece PDF kabul et
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Lütfen PDF dosyası yükleyin.")

    try:
        # Geçici input klasörü
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(base_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Dosyayı benzersiz isimle kaydet
        temp_name = f"{uuid4().hex}.pdf"
        input_path = os.path.join(uploads_dir, temp_name)

        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Çıktı klasörü
        output_dir = os.path.join(base_dir, "Çıktılar")

        # PDF'i işle
        result = process_pdf(input_path, output_dir)

        # İşlenmiş PDF'i base64'e çevir
        processed_file_base64 = None
        if result.get("output_path") and os.path.exists(result["output_path"]):
            with open(result["output_path"], "rb") as pdf_file:
                processed_file_base64 = base64.b64encode(pdf_file.read()).decode("utf-8")
        
        # Geçici dosyaları temizle
        if os.path.exists(input_path):
            os.remove(input_path)

        return {
            "success": True,  # Dosya işlendiyse her zaman True
            "full_name": result.get("full_name"),
            "output_filename": result.get("filename"),
            "processed_file_base64": processed_file_base64,  # KRİTİK: Bu alan eklendi!
            "full_name_found": result.get("success", False),  # Full name bulundu mu?
        }

    except Exception as e:
        # Hata durumunda bile anlamlı response dön
        return {
            "success": False,
            "error": str(e),
            "processed_file_base64": None,
        }
