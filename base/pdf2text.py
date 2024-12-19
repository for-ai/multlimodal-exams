import argparse
import json
from pathlib import Path
from pdf2image import convert_from_path
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTFigure
import pymupdf
from sklearn.cluster import DBSCAN


# Function to combine bounding boxes
def combine_bounding_boxes(bounding_boxes):
    x0 = min(box[0] for box in bounding_boxes)
    y0 = min(box[1] for box in bounding_boxes)
    x1 = max(box[2] for box in bounding_boxes)
    y1 = max(box[3] for box in bounding_boxes)
    return x0, y0, x1, y1


class Figure:
    def __init__(self, elements):
        self.elements = elements
        self.bbox = self._combine_bounding_boxes([el.bbox for el in elements])

    def _combine_bounding_boxes(self, bounding_boxes):
        x0 = min(box[0] for box in bounding_boxes)
        y0 = min(box[1] for box in bounding_boxes)
        x1 = max(box[2] for box in bounding_boxes)
        y1 = max(box[3] for box in bounding_boxes)
        return x0, y0, x1, y1


class Table:
    def __init__(self, bbox):
        self.bbox = bbox


# Function to apply clustering on bounding boxes
def cluster_figures(elements, eps=300):
    centers = [
        (element.bbox[0], element.bbox[1]) for element in elements
    ]  # Bottom-left corner as coordinates
    clustering = DBSCAN(eps=eps, min_samples=2).fit(centers)
    clusters = {}
    for idx, label in enumerate(clustering.labels_):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(elements[idx])
    figures = []
    for label, cluster in clusters.items():
        figures.append(Figure(cluster))
    return figures


def sort_bounding_boxes(objects, y_tolerance=5):
    # Sort by y1 first (top-to-bottom), then by x0 (left-to-right)
    return sorted(
        objects, key=lambda obj: (round(-obj.bbox[3] / y_tolerance), obj.bbox[0])
    )


def extract_pdf_content(pdf_file, output_dir, args):

    # Prepare output paths
    images_folder = output_dir / "images"
    images_folder.mkdir(exist_ok=True)

    # Inidialize PDF handlers
    pdf = open(pdf_file, "rb")
    parser = PDFParser(pdf)
    doc = PDFDocument(parser)
    parser.set_document(doc)
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pymupdf_doc = pymupdf.open(pdf_file)

    result = []
    for page_num, page in enumerate(PDFPage.create_pages(doc)):
        # Get layout
        page_image = convert_from_path(
            pdf_file,
            first_page=page_num,
            last_page=page_num + 1,
            size=(page.mediabox[2], page.mediabox[3]),
        )[0]
        interpreter.process_page(page)
        layout = device.get_result()

        # Extract layout elements
        lt_objs = [element for element in layout]
        figures = [element for element in lt_objs if isinstance(element, (LTFigure))]
        tables = [Table(table.bbox) for table in pymupdf_doc[page_num].find_tables()]

        if figures:
            clustered_figures = cluster_figures(figures, eps=args.cluster_margin)
            lt_objs = [element for element in lt_objs if element not in figures]
            for figure in clustered_figures:
                lt_objs.append(figure)
        if tables:
            for table in tables:
                lt_objs.append(table)
        sorted_lt = sort_bounding_boxes(lt_objs)

        # Create output layout
        page_content = []
        for t, element in enumerate(sorted_lt):
            if isinstance(element, (LTTextBox)):  # Add other types if needed
                page_content.append(element.get_text().strip())

            if isinstance(element, Figure):
                image_name = f"image_page-{page_num}_im-{t}.jpg"
                page_content.append(f"<image>{image_name}</image>")
                x0, y0, x1, y1 = element.bbox
                image_height = page_image.height
                crop_box = (x0, image_height - y1, x1, image_height - y0)
                cropped_image = page_image.crop(crop_box)
                cropped_image.save(images_folder / image_name)

            if isinstance(element, Table):
                table_name = f"table_page-{page_num}_im-{t}.jpg"
                page_content.append(f"<image>{table_name}</image>")
                pix = pymupdf_doc[page_num].get_pixmap(clip=table.bbox)
                pix.save(images_folder / table_name)

        page_content = " ".join(page_content)
        result.append({"page": page_num + 1, "content": page_content})
    return result


def main():
    args = parse_args()
    pdf_file = Path(args.pdf_path)

    # Prepare output paths
    if output_dir is None:
        output_dir = pdf_file.parent / pdf_file.stem
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    content = extract_pdf_content(pdf_file, output_dir, args)
    output_file = Path(output_dir) / "document_content.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(content, json_file, ensure_ascii=False, indent=4)


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
    parser.add_argument(
        "--cluster_margin",
        type=int,
        default=50,
        help="Marging for the clustering algorithm",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
