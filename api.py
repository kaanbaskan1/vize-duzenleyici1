import os
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException

from pdf_processor import process_pdf

app = FastAPI(title="Vize PDF Düzenleyici API")


@app.get("/")
def root():
    return {"message": "Vize PDF düzenleyici servis çalışıyor."}


@app.post("/process")
async def process_pdf_endpoint(file: UploadFile = File(...)):
    # Sadece PDF kabul et
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Lütfen PDF dosyası yükleyin.")

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

    return {
        "success": result["success"],
        "full_name": result["full_name"],
        "output_filename": result["filename"],
        "output_folder": "Çıktılar",
        "note": "Çıktı dosyaları sunucu tarafında tutuluyor.",
    }
