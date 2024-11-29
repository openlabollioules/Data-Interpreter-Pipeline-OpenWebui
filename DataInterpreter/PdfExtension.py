from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from PIL import Image
from pdfminer.layout import LAParams
import pytesseract
import fitz
import io
from PIL import Image, ImageEnhance, ImageFilter
import os


def extract_pdf(filepath):
    """Extrait le texte et les images d'un PDF, y compris le texte OCR des images."""
    # Extraction du texte et des images du PDF
    extracted_text = []
    images_data = []

    if not os.path.exists(filepath):
        print(f"Le fichier '{filepath}' n'existe pas au moment de l'accès.")
        raise HTTPException(
            status_code=500, detail=f"Le fichier '{filepath}' n'existe pas."
        )

    # Vérifier les permissions du fichier
    print(f"Permissions du fichier '{filepath}': {oct(os.stat(filepath).st_mode)[-3:]}")

    # Ouvrir le document PDF avec PyMuPDF (fitz)
    pdf_document = fitz.open(filepath)
    print(f"Number of pages in PDF '{filepath}': {len(pdf_document)}")

    for page_num in range(len(pdf_document)):
        # Extraction du texte de la page avec PyMuPDF
        try:
            page = pdf_document.load_page(page_num)
            pdf_text = page.get_text()
            if pdf_text.strip():
                print(
                    f"Text extracted from page {page_num} of PDF '{filepath}':\n{pdf_text[:200]}..."
                )  # Print first 200 characters
                extracted_text.append({"page": page_num, "content": pdf_text})
            else:
                print(f"No text extracted from page {page_num} of PDF '{filepath}'.")
        except Exception as e:
            print(
                f"Error extracting text from page {page_num} of PDF '{filepath}': {e}"
            )
            continue

        # Extraction des images de la page
        images = page.get_images(full=True)
        print(f"Found {len(images)} images on page {page_num} of PDF '{filepath}'.")

        for img_index, img in enumerate(images):
            try:
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))

                image = image.convert("L")
                image = ImageEnhance.Contrast(image).enhance(2)
                image = image.filter(ImageFilter.SHARPEN)
                image = image.resize((image.width * 2, image.height * 2))

                # Utilisation d'OCR pour extraire le texte des images (si nécessaire)
                ocr_text = pytesseract.image_to_string(
                    image, config="--psm 6", lang="eng"
                )
                if ocr_text.strip():
                    print(
                        f"OCR text extracted from image {img_index} on page {page_num} of PDF:\n{ocr_text[:200]}..."
                    )  # Print first 200 characters
                else:
                    print(
                        f"No OCR text extracted from image {img_index} on page {page_num} of PDF."
                    )

                images_data.append(
                    {"page": page_num, "image_index": img_index, "ocr_text": ocr_text}
                )
            except Exception as e:
                print(
                    f"Error processing image {img_index} on page {page_num} of PDF '{filepath}': {e}"
                )
                continue

    return extracted_text, images_data
