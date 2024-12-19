"""
PDF Content Extractor with PyMuPDF

This script processes a PDF file to extract its text, images, and tables, and organizes the results into an output directory. 
It utilizes the PyMuPDF library (pymupdf) for PDF parsing and extraction.

Key Features:
1. **Text Extraction**: Extracts all text content from each page in the PDF.
2. **Image Extraction**: Extracts images embedded within the PDF and saves them as separate image files.
3. **Table Extraction**: Detects and extracts tables from the PDF pages, saving table regions as images.
4. **JSON Layout Representation**: Outputs a structured JSON file (`pages_content.json`) containing:
   - Page numbers
   - Extracted text
   - Paths to saved images
   - Paths to saved table images

### Output Structure:
A directory with the following:
- A subdirectory named `images/` containing extracted images and tables saved as image files.
- A JSON file `pages_content.json` representing the layout of each page, including text, image paths, and table paths.

### How to Use:
Run the script with the following arguments:
    --pdf_path: Path to the input PDF file.
    --output_dir: Directory to save the extracted content.

Example:
    python script.py --pdf_path "path/to/input.pdf" --output_dir "path/to/output_dir"
"""

import argparse
import json
from pathlib import Path
import pymupdf
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="PDF to Text")
    parser.add_argument(
        "--pdf_path",
        type=str,
        required=True,
        help="Path to the PDF file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Directory to store results",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    pdf_file = Path(args.pdf_path)
    doc = pymupdf.open(pdf_file)

    if output_dir is None:
        output_dir = pdf_file.parent / pdf_file.stem
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    images_folder = output_dir / "images"
    images_folder.mkdir(exist_ok=True)

    pages_content = []
    for page_num, page in tqdm(enumerate(doc, start=1)):
        page_content = {"page_number": page_num, "layout": []}

        page_layout = page_content["layout"]
        text = page.get_text()
        page_layout.append({"type": "text", "content": text})

        images = page.get_images(full=True)
        for img_num, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_format = base_image["ext"]
            img_bytes = base_image["image"]

            image_name = f"image_page{page_num}_im{img_num}.{img_format}"
            image_path = images_folder / image_name

            with open(image_path, "wb") as img_file:
                img_file.write(img_bytes)

            page_layout.append({"type": "image", "content": str(image_path)})

        tables = page.find_tables()
        for tab_num, table in enumerate(tables):
            table_name = f"table_page{page_num}_im{tab_num}.png"
            pix = page.get_pixmap(clip=table.bbox)
            table_path = images_folder / table_name
            pix.save(table_path)
            page_layout.append({"type": "table", "content": str(table_path)})
        pages_content.append(page_content)

    layout_file = output_dir / "pages_content.json"
    with open(layout_file, "w", encoding="utf-8") as json_file:
        json.dump(pages_content, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
