import os
import pytesseract
import time
import psutil
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import streamlit as st

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración de TESSDATA_PREFIX en el código
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

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
    "total_errors": 0,
    "cpu_usage": 0,
    "memory_usage": 0,
    "output_pdf_size": 0
}

def preprocess_image(image):
    """Mejora la imagen para una mejor precisión de OCR"""
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Aumentar el contraste
    image = image.convert("L")   # Convertir a escala de grises
    return image

def convert_pdf_to_images(pdf_path):
    """Convierte un archivo PDF en una lista de imágenes"""
    return convert_from_path(pdf_path)

def ocr_image(image):
    """Realiza OCR en una imagen y devuelve el texto extraído"""
    try:
        image = preprocess_image(image)  # Aplica preprocesamiento
        text = pytesseract.image_to_string(image, lang='spa')
        return text.strip()  # Eliminamos espacios en blanco al inicio y final
    except Exception as e:
        st.error(f"Error en OCR: {e}")
        return ""

def save_text_to_pdf(all_pages_text, output_path):
    """Guarda el texto extraído en un archivo PDF con tamaño Carta, respetando la estructura de páginas y evitando páginas en blanco."""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Márgenes y configuración de línea
    left_margin = 50
    top_margin = height - 50
    line_height = 12
    max_lines_per_page = int((height - 100) / line_height)

    for page_number, page_text in enumerate(all_pages_text, start=1):
        print(f"\nProcessing page {page_number}")
        text_object = c.beginText(left_margin, top_margin)
        text_object.setFont("Helvetica", 10)

        # Dividir el texto en líneas y contar
        lines = page_text.splitlines()
        print(f"Number of lines on page {page_number}: {len(lines)}")

        line_count = 0
        for line in lines:
            if line_count >= max_lines_per_page:
                c.drawText(text_object)
                c.showPage()
                text_object = c.beginText(left_margin, top_margin)
                text_object.setFont("Helvetica", 10)
                line_count = 0

            if line.strip():  # Solo agregar líneas no vacías
                print(f"Adding line to page {page_number}: {line}")
                text_object.textLine(line)
                line_count += 1

        # Finaliza la página actual solo si contiene texto
        if line_count > 0:
            c.drawText(text_object)
            c.showPage()

    # Guardar el archivo PDF
    c.save()
    print("PDF generation completed.")

def process_pdf(pdf_path, output_path):
    """Convierte un PDF a imágenes, realiza OCR, y guarda el texto en un nuevo PDF"""
    try:
        start_time = time.time()
        images = convert_pdf_to_images(pdf_path)
        all_pages_text = []
        process = psutil.Process()

        for i, image in enumerate(images):
            page_start_time = time.time()
            page_text = ocr_image(image)
            all_pages_text.append(page_text)  # Agregar cada página OCR como un elemento en la lista
            metrics["pages_processed"] += 1
            metrics["average_time_per_page"] += (time.time() - page_start_time)

            metrics["cpu_usage"] += process.cpu_percent()
            metrics["memory_usage"] += process.memory_info().rss / (1024 * 1024)

        metrics["average_time_per_page"] /= metrics["pages_processed"]
        metrics["total_time"] = time.time() - start_time
        metrics["cpu_usage"] /= metrics["pages_processed"]
        metrics["memory_usage"] /= metrics["pages_processed"]

        # Guardar todo el texto extraído en un PDF con formato Carta
        save_text_to_pdf(all_pages_text, output_path)
        metrics["output_pdf_size"] = os.path.getsize(output_path) / 1024
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
    st.write(f"- Uso promedio de CPU: {metrics['cpu_usage']:.2f}%")
    st.write(f"- Uso promedio de Memoria: {metrics['memory_usage']:.2f} MB")
    st.write(f"- Tamaño del PDF resultante: {metrics['output_pdf_size']:.2f} KB")

# Interfaz de Streamlit
st.title("OCR de PDF a Texto con Métricas")
uploaded_file = st.file_uploader("Sube un archivo PDF", type="pdf")

if uploaded_file is not None:
    input_path = os.path.join(input_dir, uploaded_file.name)
    output_path = os.path.join(output_dir, uploaded_file.name.replace('.pdf', '_text.pdf'))

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Procesa el PDF subido
    if process_pdf(input_path, output_path):
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
