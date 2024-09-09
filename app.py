import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import streamlit as st

# ConfTesseract (ruta según entorno)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Conf directorios
input_dir = "input_documents"
output_dir = "output_documents"
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

def convert_pdf_to_images(pdf_path):
    """Convierte un archivo PDF en una lista de imágenes"""
    return convert_from_path(pdf_path)

def ocr_image(image):
    """Realiza OCR en una imagen y devuelve el texto extraído, especificando el idioma español"""
    text = pytesseract.image_to_string(image)  
    return text

def save_text_to_pdf(text, output_path):
    """Guarda el texto extraído en un archivo PDF con formato apropiado"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    text_object = c.beginText(50, height - 50)
    text_object.setFont("Helvetica", 10)

    # Añadir texto línea por línea para evitar caracteres incorrectos
    for line in text.split('\n'):
        text_object.textLine(line)
    
    c.drawText(text_object)
    c.save()

def process_pdf(pdf_path, output_path):
    """Convierte un PDF a imágenes, realiza OCR, y guarda el texto en un nuevo PDF"""
    try:
        images = convert_pdf_to_images(pdf_path)
        all_text = ""
        for image in images:
            all_text += ocr_image(image) + "\n"
        save_text_to_pdf(all_text, output_path)
        return True
    except Exception as e:
        st.error(f"Error al procesar el PDF: {e}")
        return False

st.title("OCR de PDF a Texto")
uploaded_file = st.file_uploader("Sube un archivo PDF", type="pdf")

if uploaded_file is not None:
    # Guarda el archivo subido en el sistema
    input_path = os.path.join(input_dir, uploaded_file.name)
    output_path = os.path.join(output_dir, uploaded_file.name.replace('.pdf', '_text.pdf'))

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Procesa el PDF subido
    if process_pdf(input_path, output_path):
        # Mostrar enlace para descargar el archivo PDF convertido
        st.write("¡Documento procesado con éxito!")
        with open(output_path, "rb") as file:
            btn = st.download_button(
                label="Descargar PDF con OCR",
                data=file,
                file_name=output_path,
                mime="application/pdf"
            )
