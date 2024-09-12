import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract
import PyPDF2
from PIL import Image as PILImage
from processing.tables_predprocessor import PDFTableExtractor
import os
import re
import json
import difflib
import matplotlib.pyplot as plt

class PDFProcessor:
    def __init__(self, tesseract_cmd='', poppler_path=''):
        """
        Инициализация класса PDFProcessor.
        :param tesseract_cmd: Путь к исполняемому файлу Tesseract OCR.
        :param poppler_path: Путь к Poppler для конвертации PDF в изображения.
        """
        if tesseract_cmd != '':
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.poppler_path = poppler_path if poppler_path else None
        self.table_extractor = PDFTableExtractor() 

    def detect_and_remove_tables(self, image: np.array) -> PILImage:
        """
        Обнаруживает таблицы на изображении и маскирует их.
        Возвращает изображение с замаскированными таблицами.
        """
    
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY_INV, 15, 9)

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)


        table_mask = cv2.add(horizontal_lines, vertical_lines)

        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.ones_like(gray) * 255

        min_table_area = 1000  
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_table_area:
                cv2.drawContours(mask, [contour], -1, 0, -1)

        result = cv2.bitwise_and(gray, gray, mask=mask)

        return PILImage.fromarray(result)


    def json_converter(self, raw_text: str, file_path: str, page_number: int, doc_type='text') -> dict:
        """
        Преобразует текст в JSON формат с метаданными.
        """
        file_name = os.path.basename(file_path)
        json_object = {
            "raw_text": raw_text,
            "file_path": file_path,
            "doc_type": doc_type,
            "filename": file_name,
            "page_number": page_number
        }
        return json_object

    def is_scanned_pdf(self, pdf_path):
        """Проверяем, является ли PDF файлом отсканированным."""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    return False 
        return True
    
    def process_pdf_page(self, pdf_path: str, page_number: int, page_count: int) -> dict:
        """
        Обрабатывает указанную страницу PDF и возвращает JSON с текстом, очищенным от таблиц.
        """

        if self.poppler_path:
            images = convert_from_path(pdf_path, poppler_path=self.poppler_path, first_page=page_number, last_page=page_number, dpi=300)
        else:
            images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number, dpi=300)
        image = images[0]
    
        if self.is_scanned_pdf(pdf_path):
            image_without_tables = image
            if(len(self.table_extractor.extract_tables_from_pdf(pdf_path, page_number, page_count, combine_tables=False))!=0):
                image_without_tables = self.detect_and_remove_tables(image)

            # plt.imshow(image_without_tables, cmap='gray')
            # plt.axis('off') 
            # plt.savefig(f'./result/images/{page_number}.png', bbox_inches='tight', pad_inches=0, dpi=300)

            filtered_text = pytesseract.image_to_string(image_without_tables, lang='rus+eng')
        else:
            raw_text  = pytesseract.image_to_string(image, lang='rus+eng')
            
            if raw_text and raw_text.strip():
                tables_ocr_text = self.table_extractor.extract_table_text(pdf_path, page_number - 1, page_count)
                raw_text = re.sub(r' \| ', ' ', raw_text)
                filtered_text = self.remove_tables_from_text(raw_text,  tables_ocr_text)
        try:
            text = self.clean_text(filtered_text)
        except:
            text = ''

        return self.json_converter(text, pdf_path, page_number)
    
    def remove_tables_from_text(self, raw_text, tables):
        """Удаляет таблицы из текста, используя результат OCR и построчное сравнение."""
        idx_to_del = []
        for table in tables:
            clean_text_lines = list(filter(lambda x: x.strip(), raw_text.splitlines()))
            table_ocr_lines = list(filter(lambda x: x.strip(), table.splitlines()))
            
            start_idx, end_idx = self.find_table_boundaries(raw_text, clean_text_lines, table_ocr_lines)
            
            if start_idx is not None and end_idx is not None:
                idx_to_del.append((start_idx, end_idx))
            else:
                idx_to_del.append((None, None))

        clean_text = self.remove_text_by_indices(raw_text, idx_to_del)
        return clean_text

    def remove_text_by_indices(self, raw_text, indices):
        """Удаляет текст из raw_text по заданным индексам."""
        if not indices :
            return raw_text
        # print(indices)

        indices = [item for item in indices if item != (None, None)]

        indices = []

        indices.sort()
        
        result = []
        last_end = 0
        
        for start_idx, end_idx in indices:
            if start_idx is None or end_idx is None:
                continue
            if last_end < start_idx:
                result.append(raw_text[last_end:start_idx])
            last_end = end_idx

        if last_end < len(raw_text):
            result.append(raw_text[last_end:])
        
        return ''.join(result)


    def find_table_boundaries(self, raw_text, text_lines, table_lines):
        """Находит индексы начала и конца таблицы в исходном тексте (raw_text)."""
        start_idx = None
        end_idx = None

        for i, line in enumerate(text_lines):
            table_cat = ""
            line_cat = ""
            
            if len(table_lines)==0:
                start_idx, end_idx = None, None
                return start_idx, end_idx
            
            if len(table_lines[0]) <= len(line):
                line_cat = line[:len(table_lines[0])]
                table_cat = table_lines[0]
            else:
                line_cat = line
                table_cat = table_lines[0][:len(line)]
            # print(line)
            # print(line_cat)
            # print(table_lines[0])
            # print(table_cat)
            # print()
            
            matches = difflib.get_close_matches(line_cat, [table_cat], n=1, cutoff=0.8)
            if matches:
                start_idx = raw_text.find(line_cat) 
                break


        for i, line in enumerate(text_lines):
            table_cat = ""
            line_cat = ""
            
            if len(table_lines[-1]) <= len(line):
                line_cat = line[:len(table_lines[-1])]
                table_cat = table_lines[-1]
            else:
                line_cat = line
                table_cat = table_lines[-1][:len(line)]

            # print(line)
            # print(line_cat)
            # print(table_lines[-1])
            # print(table_cat)
            # print()
            
            matches = difflib.get_close_matches(line_cat, [table_cat], n=1, cutoff=0.8)
            if matches:
                end_idx = raw_text.find(line_cat) + len(line) 
                break  

        return start_idx, end_idx
    
    def clean_text(self, text: str) -> str:
            
        text = re.sub(r'(?<=\S)-\n(?=\S)', '', text)

        text = re.sub(r'(\s)П(\s)', r'\1II\2', text)  
        text = re.sub(r'(\s)П,', r'\1II,', text)      
        text = re.sub(r',П(\s)', r',II\1', text)     
        text = re.sub(r'(\s)Ш(\s)', r'\1III\2', text)  
        text = re.sub(r'(\s)Ш,', r'\1III,', text)     
        text = re.sub(r',Ш(\s)', r',III\1', text)      

        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\bTig\b|[\x0c]', '', text)
        text = re.sub(r'\|', '', text)
        text = re.sub(r'-ro', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_image(self, pdf_path: str, page_number: int) -> dict:
        """
        Обрабатывает указанную страницу PDF и возвращает JSON с текстом, очищенным от таблиц.
        """

        if self.poppler_path:
            images = convert_from_path(pdf_path, poppler_path=self.poppler_path, first_page=page_number, last_page=page_number, dpi=300)
        else:
            images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number, dpi=300)
        
        image = images[0]

        return image

if __name__ == "__main__":
    poppler_path = r'C:/poppler-24.02.0/Library/bin'
    pdf_path = 'example.pdf'
    page_number = 12

    processor = PDFProcessor(poppler_path=poppler_path)
    result = processor.process_pdf_page(pdf_path, page_number)
    print(json.dumps(result, indent=4, ensure_ascii=False))
