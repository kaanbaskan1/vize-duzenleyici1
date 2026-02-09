from flask import Flask, request, jsonify
import tempfile
import os
import base64
import logging
from pdf_processor import process_pdf, extract_full_name, sanitize_filename

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/process", methods=["POST"])
def process():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"})

        file = request.files["file"]
        logger.info(f"Received file: {file.filename}, size: {file.content_length}")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            file.save(input_path)

            full_name = extract_full_name(input_path)
            logger.info(f"Extracted full name: {full_name}")

            process_pdf(input_path, output_path)

            with open(output_path, "rb") as f:
                processed_base64 = base64.b64encode(f.read()).decode()

            sanitized = sanitize_filename(full_name) if full_name else None
            output_filename = f"{sanitized}.pdf" if sanitized else file.filename

            logger.info(f"Processing complete. Output: {output_filename}")

            return jsonify({
                "success": True,
                "processed_file_base64": processed_base64,
                "full_name": full_name,
                "full_name_found": full_name is not None,
                "output_filename": output_filename,
            })
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "full_name": None,
            "output_filename": None,
            "processed_file_base64": None,
            "full_name_found": False,
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
