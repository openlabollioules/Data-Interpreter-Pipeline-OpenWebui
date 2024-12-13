from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from PIL import Image
from pdfminer.layout import LAParams
import pytesseract
import fitz
import io
from PIL import Image, ImageEnhance, ImageFilter
import os
import re
import pandas as pd
import numpy as np
import base64

# tesseract_path = "/usr/local/shared_tesseract/tesseract"
# pytesseract.pytesseract.tesseract_cmd = tesseract_path


def consolidate_results(raw_results):
    """
    Regroupe les résultats pour éviter les répétitions et conserve uniquement les informations pertinentes.
    """
    consolidated = {
        "format": None,
        "dimensions": None,
        "text_detected": [],
        "description": [],
    }

    for result in raw_results:
        if "PNG" in result.get("format", ""):
            consolidated["format"] = "PNG"
        if result.get("dimensions"):
            consolidated["dimensions"] = result["dimensions"]
        if result.get("text_detected"):
            consolidated["text_detected"].append(result["text_detected"])
        if result.get("description"):
            consolidated["description"].append(result["description"])

    # Nettoyer les champs
    consolidated["text_detected"] = list(set(consolidated["text_detected"]))
    consolidated["description"] = list(set(consolidated["description"]))
    return consolidated


def format_final_output(consolidated_result):
    """
    Génère une sortie formatée pour une image donnée.
    """
    output = f"Format : {consolidated_result['format'] or 'Inconnu'}\n"
    if consolidated_result["dimensions"]:
        output += f"Dimensions : {consolidated_result['dimensions']}\n"
    if consolidated_result["text_detected"]:
        output += f"Texte détecté : {', '.join(consolidated_result['text_detected'])}\n"
    if consolidated_result["description"]:
        output += f"Description : {'; '.join(consolidated_result['description'])}\n"
    else:
        output += "Description : Aucune information visuelle pertinente détectée.\n"
    return output


def process_images_with_ollama_invoke(image_bytes, ollama_model):
    """
    Analyse une image via Ollama Vision et gère les différents formats de réponse.
    """
    try:
        # Encodage de l'image en base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = f"""
            Analyse l'image suivante encodée en base64 et fournis uniquement les informations demandées dans une structure claire.
            
            Image encodée : {image_base64}
            
            Limite ta réponse à 800 caractères maximum et suis strictement cette structure :
            
            1. **Format de l'image** : (ex. PNG, JPEG, etc.)
            2. **Dimensions de l'image** : (ex. 128x128 pixels)
            3. **Contenu détecté** : (ex. texte, graphique, ou aucun contenu)
            4. **Description concise** : (ex. "Image vide" ou "Logo avec texte 'Hello World'")
            
            Si aucune donnée n'est détectée, indique simplement "Aucun contenu détecté". Ne répète pas les informations. 
            """

        # Appel au modèle Ollama Vision
        result = ollama_model.invoke(prompt)
        print(f"Résultat brut de Llama Vision : {result}")

        # Gestion des types de réponse
        if isinstance(result, str):
            # Si réponse est une chaîne, la retourner comme texte brut
            return {"description": result}
        elif isinstance(result, dict):
            # Si réponse est un dictionnaire, l'utiliser directement
            return result
        else:
            # Gestion des types inattendus
            return {"error": f"Type de réponse inattendu : {type(result)}"}
    except Exception as e:
        print(f"Erreur lors du traitement de l'image avec Ollama : {e}")
        return {"error": str(e)}


def is_empty_image(image_bytes):
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Vérifiez la taille
            if img.size[0] < 10 or img.size[1] < 10:  # Très petite image
                return True

            # Analyse des couleurs uniques
            pixels = np.array(img)
            unique_colors = len(np.unique(pixels.reshape(-1, pixels.shape[-1]), axis=0))
            if unique_colors <= 5:  # Par exemple, moins de 5 couleurs
                return True

        return False
    except Exception as e:
        print(f"Erreur lors de l'analyse de l'image : {e}")
        return False


def detect_text_in_image(image_bytes):
    """
    Détecte le texte dans une image via Tesseract OCR.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            text = pytesseract.image_to_string(img)
            return text.strip()
    except Exception as e:
        print(f"Erreur lors de la détection du texte : {e}")
        return None


def extract_pdf(filepath, ollama_model):
    """Extrait le texte et analyse les images d'un PDF via Ollama Vision."""
    extracted_text = []
    images_data = []

    if not os.path.exists(filepath):
        print(f"Le fichier '{filepath}' n'existe pas.")
        raise FileNotFoundError(f"Le fichier '{filepath}' n'existe pas.")

    print(f"Processing PDF file: {filepath}")
    pdf_document = fitz.open(filepath)
    print(f"Number of pages in PDF: {len(pdf_document)}")

    for page_num in range(len(pdf_document)):
        # Extraction du texte
        try:
            page = pdf_document.load_page(page_num)
            pdf_text = page.get_text()
            if pdf_text.strip():
                extracted_text.append({"page": page_num, "content": pdf_text})
        except Exception as e:
            print(f"Error extracting text from page {page_num}: {e}")
            continue

        # Extraction des images
        images = page.get_images(full=True)
        print(f"Found {len(images)} images on page {page_num}.")

        for img_index, img in enumerate(images):
            try:
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # Vérification des données d'image
                if not image_bytes or len(image_bytes) < 10:
                    print(
                        f"L'image {img_index} semble corrompue ou est extrêmement petite."
                    )
                    continue

                if is_empty_image(image_bytes):
                    print(f"Image {img_index} est vide ou sans contenu pertinent.")
                    continue

                # Vérification et extraction du texte avec OCR
                text = detect_text_in_image(image_bytes)
                if text:
                    print(f"Texte détecté dans l'image {img_index} : {text}")
                    images_data.append(
                        {
                            "page": page_num,
                            "image_index": img_index,
                            "text": text,
                            "result": "Texte détecté uniquement via OCR.",
                        }
                    )
                    continue

                # Encodage de l'image en base64 pour Ollama
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                # Analyse de l'image via Ollama Vision
                llama_result = process_images_with_ollama_invoke(
                    image_bytes, ollama_model
                )

                # Consolidation des résultats
                consolidated_result = consolidate_results([llama_result])

                # Génération de la sortie finale formatée
                final_output = format_final_output(consolidated_result)

                # Vérification des résultats
                if "error" in llama_result:
                    print(
                        f"Error processing image {img_index}: {llama_result['error']}"
                    )
                else:
                    images_data.append(
                        {
                            "page": page_num,
                            "image_index": img_index,
                            "result": final_output,
                        }
                    )
            except Exception as e:
                print(f"Error processing image {img_index} on page {page_num}: {e}")
                continue

    return extracted_text, images_data
