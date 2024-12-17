import argparse
from binascii import b2a_hex
from pdfminer.image import ImageWriter
import io
from PIL import Image
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar
from pathlib import Path


def save_figure(lt_figure, page_number, page_render, images_folder):
    """
    Save an LTFigure object from the page image. Use

    Args:
        lt_figure (LTFigure): An figure object from pdfminer layout analysis.
        page_number (int): The page number where the image was found.
        page_render (list[PIL]): List with images of the pdf pages to crop.
        images_folder (str): Path to the folder where images will be saved.

    Returns:
        str: Name of the saved file, or None if saving failed.
    """
    pass


def save_image(lt_image, page_number, images_folder):
    """
    Save the image data from an LTImage object to a file.

    Args:
        lt_image (LTImage): An image object from pdfminer layout analysis.
        page_number (int): The page number where the image was found.
        images_folder (str): Path to the folder where images will be saved.

    Returns:
        str: Name of the saved file, or None if saving failed.
    """
    result = None

    # Create an ImageWriter for the specified folder
    iw = ImageWriter(images_folder)

    try:
        # Export the image and get the default filename
        lt_image.name = f"{page_number}_{lt_image.name}"
        default_file = iw.export_image(lt_image)
        if not default_file:
            return None
        return default_file
    except Exception as e:
        print(f"Error saving image on page {page_number}: {e}")
        return None


def parse_lt_objs(lt_objs, page_number, images_folder, text_content=None):
    """
    Iterate through the list of LT* objects and capture the text or image data contained in each.
    """
    if text_content is None:
        text_content = []

    page_text = (
        {}
    )  # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
    for lt_obj in lt_objs:
        if isinstance(lt_obj, (LTTextBox, LTTextLine)):
            # Text object: add its text to the page_text hash based on its column width
            page_text = update_page_text_hash(page_text, lt_obj)
        elif isinstance(lt_obj, LTImage):
            # Image object: save it and add an HTML-style placeholder
            saved_file = save_image(lt_obj, page_number, images_folder)
            if saved_file:
                # Use HTML-style <img> tag to mark the position of the image in the text
                text_content.append(f'<img src="{saved_file}" />')
            else:
                print(f"Error saving image on page {page_number}: {lt_obj}")
        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects; recurse into children
            parse_lt_objs(lt_obj, page_number, images_folder, text_content)

    # Append the text from the page_text hash, sorted by the bbox keys
    for k, v in page_text.items():
        # Sort by bbox coordinates and join text from the same column
        text_content.append("".join(v))

    return "\n".join(text_content)


def _parse_pages(doc, images_folder):
    """With an open PDFDocument object, get the pages and parse each one."""
    # Set up resources and interpreter
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    text_content = []
    image_folder = Path(images_folder)
    image_folder.mkdir(parents=True, exist_ok=True)

    for i, page in enumerate(PDFPage.create_pages(doc)):
        interpreter.process_page(page)
        # Receive the LTPage object for this page
        layout = device.get_result()
        # Parse layout objects (text, images, etc.)
        page_text = parse_lt_objs(layout, (i + 1), images_folder)
        text_content.append(page_text)
    return text_content


def with_pdf(pdf_doc, fn, *args):
    """Open the PDF document, and apply the function, returning the results"""
    result = None
    try:
        # Open the PDF file
        with open(pdf_doc, "rb") as fp:
            # Create a parser object associated with the file object
            parser = PDFParser(fp)
            # Create a PDFDocument object that stores the document structure
            doc = PDFDocument(parser)
            # Supply the password for initialization
            parser.set_document(doc)

            if doc.is_extractable:
                # Apply the function and return the result
                result = fn(doc, *args)
    except Exception as e:
        print(f"Error processing file {pdf_doc}: {e}")
    return result


def get_pages(pdf_doc, images_folder="/content/tmp"):
    """Process each of the pages in this pdf file and return the extracted text."""
    return with_pdf(pdf_doc, _parse_pages, *tuple([images_folder]))


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
        required=True,
        help="Directory to store results",
    )
    args = parser.parse_args()
    return args


def main():
    pass


if __name__ == "__main__":
    main()
