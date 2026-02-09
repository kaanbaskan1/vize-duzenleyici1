# -*- coding: utf-8 -*-
import os
import base64
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException

from pdf_processor import process_pdf

app = FastAPI(title="Vize PDF Duzenleyici API")


@app.get("/")
def root():
    return {"message": "Vize PDF duzenleyici servis calisiyor."}


@app.post("/process")
async def process_pdf_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Lutfen PDF dosyasi yukleyin.")

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(base_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        temp_name = f"{uuid4().hex}.pdf"
        input_path = os.path.join(uploads_dir, temp_name)

        with open(input_path, "wb") as f:
            f.write(await file.read())

        output_dir = os.path.join(base_dir, "output")

        result = process_pdf(input_path, output_dir)

        processed_file_base64 = None
        output_path = result.get("output_path")

        if output_path and os.path.exists(output_path):
            with open(output_path, "rb") as pdf_file:
                processed_file_base64 = base64.b64encode(pdf_file.read()).decode("utf-8")

        if os.path.exists(input_path):
            os.remove(input_path)

        return {
            "success": True,
            "full_name": result.get("full_name"),
            "output_filename": result.get("filename"),
            "processed_file_base64": processed_file_base64,
            "full_name_found": result.get("success", False),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "full_name": None,
            "output_filename": None,
            "processed_file_base64": None,
            "full_name_found": False,
        }


@app.post("/debug")
async def debug_pdf(file: UploadFile = File(...)):
    """PDF icindeki raw text encoding'ini gosterir - regex ayarlamak icin kullan"""
    import pikepdf

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Lutfen PDF dosyasi yukleyin.")

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(base_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        temp_name = f"{uuid4().hex}.pdf"
        input_path = os.path.join(uploads_dir, temp_name)

        with open(input_path, "wb") as f:
            f.write(await file.read())

        pdf = pikepdf.open(input_path)
        streams = []

        for i, page in enumerate(pdf.pages):
            page_data = {"page": i + 1, "raw_snippets": []}
            contents = page.get("/Contents")

            if contents is None:
                page_data["raw_snippets"].append("(no content stream)")
                streams.append(page_data)
                continue

            # Contents tek stream veya array olabilir
            if isinstance(contents, pikepdf.Array):
                content_list = list(contents)
            else:
                content_list = [contents]

            for obj in content_list:
                try:
                    raw = obj.read_bytes().decode("latin-1", errors="replace")
                    # Sadece text operatorlerini al (TJ, Tj iceren satirlar)
                    lines = raw.split("\n")
                    text_lines = [
                        ln.strip() for ln in lines
                        if "TJ" in ln or "Tj" in ln or "BT" in ln or "ET" in ln
                    ]
                    # Ilk 50 satir yeterli
                    page_data["raw_snippets"].extend(text_lines[:50])
                except Exception as e:
                    page_data["raw_snippets"].append(f"(read error: {e})")

            streams.append(page_data)

        pdf.close()

        if os.path.exists(input_path):
            os.remove(input_path)

        return {"success": True, "pages": streams}

    except Exception as e:
        return {"success": False, "error": str(e)}
