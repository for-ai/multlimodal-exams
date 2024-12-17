## Multimodal Multilingual Global Exams (Preliminary Version)

This repository contains a **preliminary version** of preprocessing scripts for the Multimodal Multilingual Global Exams project for extracting text, images, and tables from PDF files.
Language-specific OCR pipeline scripts will be added to this repository as they are developed.
Feel free to add specific scripts for your language! You can use the base script.
It is intended to serve as a template for implementing more advanced PDF parsing functionality.

## Features
- **Text Extraction**: Reads and saves all text content from each page of a PDF.
- **Image Extraction**: Extracts images from PDF pages and saves them as individual files.
- **Table Extraction**: Detects tables on PDF pages and saves their regions as images.
- **JSON Layout**: Outputs a structured JSON file containing:
  - Page numbers
  - Extracted text
  - Paths to extracted images and tables.

## Current Limitations
This is a preliminary version with the following known limitations:
1. **Dividing Graphs into Subgraphs**: Graphs or charts are splited into separate, smaller images.
2. **Reading Nonexistent Images**: The script may detect and attempt to read images that don’t exist, leading to black images being stored.
3. **Poor Equation Parsing**: Mathematical equations are not accurately parsed or extracted.
4. **High Dependence on LLMs for Structure**: The script currently relies on a large language model (LLM) to parse the JSON structure and place images in the correct locations. This approach can be improved by incorporating PDFMiner.six for more accurate and reliable layout and text extraction. (Will be availble soon)

## Recommendations
If you’re exploring PDF parsing, consider looking into:
- **[PyMuPDF (pymupdf)](https://pymupdf.readthedocs.io/en/latest/)**: A powerful library for PDF content extraction, including text, images, and annotations.
- **[PDFMiner.six](https://pdfminersix.readthedocs.io/en/latest/)**: Another versatile library for text extraction and layout analysis from PDFs.