import os
import pytesseract
import time
from pdf2image import convert_from_path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import streamlit as st

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración de directorios
input_dir = "input_documents"
output_dir = "output_documents"
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Métricas
metrics = {
    "total_time": 0,
    "pages_processed": 0,
    "average_time_per_page": 0,
    "total_errors": 0
}

def convert_pdf_to_images(pdf_path):
    """Convierte un archivo PDF en una lista de imágenes"""
    return convert_from_path(pdf_path)

def ocr_image(image):
    """Realiza OCR en una imagen y devuelve el texto extraído"""
    try:

        text = pytesseract.image_to_string(image, lang='spa')
        return text
    except Exception as e:
        st.error(f"Error en OCR: {e}")
        return ""

def save_text_to_pdf(text, output_path):
    """Guarda el texto extraído en un archivo PDF con formato Carta y evita cortes de párrafos"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    text_object = c.beginText(50, height - 50)
    text_object.setFont("Helvetica", 10)
    
    lines_per_page = 70  
    line_height = 12  

    lines = text.split('\n')
    line_count = 0

    for i, line in enumerate(lines):
        if line_count >= lines_per_page - 3:
            c.drawText(text_object)
            c.showPage()  
            text_object.setFont("Helvetica", 10)
            line_count = 0

        text_object.textLine(line)
        line_count += 1

    c.drawText(text_object)
    c.save()


def process_pdf(pdf_path, output_path):
    """Convierte un PDF a imágenes, realiza OCR, y guarda el texto en un nuevo PDF"""
    try:
        start_time = time.time()
        images = convert_pdf_to_images(pdf_path)
        all_text = ""
        for i, image in enumerate(images):
            page_start_time = time.time()
            page_text = ocr_image(image)
            if "6" in page_text:  # Contar posibles errores de conversión de "ñ"
                metrics["total_errors"] += page_text.count("6")
            all_text += page_text + "\n\n"
            metrics["pages_processed"] += 1
            metrics["average_time_per_page"] += (time.time() - page_start_time)

        metrics["average_time_per_page"] /= metrics["pages_processed"]
        metrics["total_time"] = time.time() - start_time

        # Guardar todo el texto extraído en un PDF con formato Carta
        save_text_to_pdf(all_text, output_path)
        return True
    except Exception as e:
        st.error(f"Error al procesar el PDF: {e}")
        return False

def display_metrics():
    """Mostrar métricas en la interfaz de Streamlit"""
    st.write("### Métricas de Conversión")
    st.write(f"- Tiempo total de procesamiento: {metrics['total_time']:.2f} segundos")
    st.write(f"- Páginas procesadas: {metrics['pages_processed']}")
    st.write(f"- Tiempo promedio por página: {metrics['average_time_per_page']:.2f} segundos")
    st.write(f"- Errores de conversión detectados (como la ñ mal interpretada): {metrics['total_errors']}")

# Interfaz de Streamlit
st.title("OCR de PDF a Texto con Métricas")
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
        # Mostrar métricas
        display_metrics()
