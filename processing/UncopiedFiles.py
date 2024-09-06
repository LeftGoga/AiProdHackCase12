import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
from time import time

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'#путь Tesseract

poppler_path = r'C:\\Users\\gleba\Downloads\\Release-24.02.0-0\\poppler-24.02.0\\Library\\bin'#путь poppler приложения для работы с pdf
pdf_path = 'data/SP.13130.2023.pdf'#путь pdf


def detect_and_remove_tables(image:np.array):
    """
    Обнаруживает таблицы на изображении и маскирует их.
    Возвращает изображение с замаскированными таблицами.
    """
    # Преобразуем изображение в оттенки серого
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Применяем бинаризацию
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    
    # Найдем горизонтальные линии
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Найдем вертикальные линии
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    
    # Объединим горизонтальные и вертикальные линии
    table_mask = horizontal_lines + vertical_lines
    
    # Найдем контуры таблиц
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Создадим маску для удаления таблиц
    mask = np.ones_like(gray) * 255  # белая маска
    for contour in contours:
        # Закрасим контуры таблиц черным цветом на маске
        cv2.drawContours(mask, [contour], -1, 0, -1)
    
    # Применим маску к изображению
    result = cv2.bitwise_and(gray, gray, mask=mask)
    
    return Image.fromarray(result)

def json_converter(raw_text:str, file_path:str, page_number:int, doc_type='text')->dict:
    file_name = os.path.basename(file_path)
    json_object = {
        "raw_text": raw_text,
        "file_path": file_path,
        "doc_type": doc_type,
        "filename": file_name,
        "page_number": page_number
        }

    return json_object

def process_pdf(pdf_path:str):
    # Конвертируем страницы PDF в изображения
    start = time()
    images = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300)
    output_json = []
    for page_num, image in enumerate(images):
        # Обрабатываем страницу для удаления таблиц
        image_without_tables = detect_and_remove_tables(image)
        
        # Применяем OCR к изображению без таблиц
        # print('begin')
        text = pytesseract.image_to_string(image_without_tables, lang='rus+eng')
        # if len(text) > 0:
        output_json.append(json_converter(text[:20], pdf_path, page_num + 1))
        # else:
            # pass
        # print('end')
    end = time()
    print(end - start)
    return output_json


print(process_pdf(pdf_path))



# Путь и номер страницы
# 