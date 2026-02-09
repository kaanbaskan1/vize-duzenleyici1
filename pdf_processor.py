import fitz
import logging

logger = logging.getLogger(__name__)


def process_pdf(input_path: str) -> str:
    """Main entry point called by api.py"""
    output_path = input_path.replace(".pdf", "_cleaned.pdf")
    
    doc = fitz.open(input_path)

    search_config = [
        {"term": "HAIR OF ISTANBUL",  "expand_right": 10},
        {"term": "TOURISM L.L.C",     "expand_right": 10},
        {"term": "Arkan Tourism LLC", "expand_right": 10},
        {"term": "M B D TOURISM",     "expand_right": 10},
        {"term": "Tel:",              "expand_right": 180},
        {"term": "TEL:",              "expand_right": 180},
        {"term": "Mob:",              "expand_right": 180},
        {"term": "P.O.BOX",          "expand_right": 180},
    ]

    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        logger.info(f"Page {page_num} text preview: {page_text[:200]}")

        for config in search_config:
            areas = page.search_for(config["term"], flags=fitz.TEXT_IGNORECASE)
            if areas:
                logger.info(f"Found '{config['term']}' {len(areas)} times on page {page_num}")
            for area in areas:
                expanded = fitz.Rect(
                    area.x0 - 2, area.y0 - 2,
                    area.x1 + config["expand_right"], area.y1 + 2
                )
                page.add_redact_annot(expanded, fill=(1, 1, 1))
        page.apply_redactions()

    doc.save(output_path)
    doc.close()
    return output_path
