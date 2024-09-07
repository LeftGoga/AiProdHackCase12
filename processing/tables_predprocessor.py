import os
import PyPDF2
import json
import difflib
import os
import fitz  
from PIL import Image as PILImage
import numpy as np
from img2table.document import Image
import io
import pytesseract

class PDFTableExtractor:

    def __init__(self, output_dir = ''):
        self.output_dir = output_dir
        
    def extract_tables_from_pdf(self, pdf_path, page_num, combine_tables=False):
        pdf_document = fitz.open(pdf_path)
        base_name = os.path.basename(pdf_path).rsplit('.', 1)[0]
        
        tables_json = self.extract_tables_on_page(pdf_document, pdf_path, page_num)
        
        if combine_tables and page_num < len(pdf_document) - 1:
            next_page_tables_json = self.extract_tables_on_page(pdf_document, pdf_path, page_num + 1)
            if next_page_tables_json:
                for current_table in tables_json:
                    for next_table in next_page_tables_json:
                        if self.is_table_continued(current_table, next_table):
                            current_table['координаты таблицы'].extend(next_table['координаты таблицы'])
                            next_page_tables_json.remove(next_table)  
            tables_json.extend(next_page_tables_json)

        pdf_document.close()
        return tables_json

    def extract_tables_on_page(self, pdf_document, pdf_path, page_num):
        """Извлекает таблицы с одной страницы PDF"""
        base_name = os.path.basename(pdf_path).rsplit('.', 1)[0]
        page = pdf_document.load_page(page_num)
        page_height = page.rect.height
        
        zoom_x = 2.0  
        zoom_y = 2.0  
        mat = fitz.Matrix(zoom_x, zoom_y)  
        pix = page.get_pixmap(matrix=mat)  
        img = PILImage.open(io.BytesIO(pix.tobytes()))  
        
        with io.BytesIO() as image_buffer:
            img.save(image_buffer, format="JPEG")
            image_buffer.seek(0)

            img_obj = Image(src=image_buffer)

            result = []
            
            try:
                extracted_tables = img_obj.extract_tables()
                
                for table_index, table in enumerate(extracted_tables):
                    
                    image_cv = np.array(img)
                    
                    min_x = min(cell.bbox.x1 for row in table.content.values() for cell in row)
                    max_x = max(cell.bbox.x2 for row in table.content.values() for cell in row)
                    min_y = min(cell.bbox.y1 for row in table.content.values() for cell in row)
                    max_y = max(cell.bbox.y2 for row in table.content.values() for cell in row)

                    coordinates = [(min_x, min_y, max_x, max_y)]

                    result.append({
                        "путь к файлу": pdf_path,
                        "имя файла": base_name,
                        "тип": "таблица",
                        "страница пдф": page_num,
                        "координаты таблицы": coordinates
                    })
                    
            except Exception as e:
                print(f"Ошибка при извлечении таблицы: {str(e)}")

        return result

    def is_table_continued(self, current_table, next_table):
        """Проверяет, продолжается ли таблица на следующей странице"""
        current_coords = current_table['координаты таблицы'][-1]
        next_coords = next_table['координаты таблицы'][0]
        
        current_max_y = current_coords[3]
        next_min_y = next_coords[1]
        
        if current_max_y >= 0.8 * current_max_y and next_min_y <= 0.2 * next_min_y:
            return True
        return False

    def extract_table_image(self, pdf_path, page_num, coordinates):
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(page_num)
        
        zoom_x = 2.0
        zoom_y = 2.0
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        img = PILImage.open(io.BytesIO(pix.tobytes()))
        
        image_cv = np.array(img)
        
        for coord in coordinates:
            min_x, min_y, max_x, max_y = coord
            table_crop = image_cv[min_y:max_y, min_x:max_x]
            
            table_image = PILImage.fromarray(table_crop)
            return table_image

        pdf_document.close()

    def extract_table_text(self, pdf_path, page_num):
        """Метод для извлечения текста таблицы с помощью OCR"""
        tables_json = self.extract_tables_from_pdf(pdf_path, page_num)
        if not tables_json:
            return "Таблицы не найдены на указанной странице."
        tables_text_list = []
        for i in range(len(tables_json)):
            coordinates = tables_json[i]["координаты таблицы"]
            table_image = self.extract_table_image(pdf_path, page_num, coordinates)
            
            ocr_text = pytesseract.image_to_string(table_image, lang='rus+eng')
            tables_text_list+=[ocr_text]
        return tables_text_list.copy()

class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
    
    def is_scanned_pdf(self):
        """Проверяем, является ли PDF файлом отсканированным."""
        with open(self.file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    return False  
        return True

    def parse_page_to_json(self, page_number, table_extractor):
        """Парсим указанную страницу PDF и возвращаем JSON, игнорируя таблицы."""
        with open(self.file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            
            if page_number < 1 or page_number > len(reader.pages):
                raise ValueError(f"Page number {page_number} is out of range.")
            
            page = reader.pages[page_number - 1]
            raw_text = page.extract_text()

            
            if raw_text and raw_text.strip():
                
                
                tables_ocr_text = table_extractor.extract_table_text(self.file_path, page_number - 1)
                
                
                clean_text = self.remove_tables_from_text(raw_text,  tables_ocr_text)

                page_data = {
                    "raw_text": clean_text.strip(),  
                    "file_path": self.file_path,
                    "doc_type": "text",
                    "filename": self.file_name,
                    "page_number": page_number
                }
                return page_data
            else:
                return {}

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
        if not indices:
            return raw_text
        
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
            
            if len(table_lines[0]) <= len(line):
                line_cat = line[:len(table_lines[0])]
                table_cat = table_lines[0]
            else:
                line_cat = line
                table_cat = table_lines[0][:len(line)]

            matches = difflib.get_close_matches(line_cat, [table_cat], n=1, cutoff=0.9)
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

            matches = difflib.get_close_matches(line_cat, [table_cat], n=1, cutoff=0.9)
            if matches:
                end_idx = raw_text.find(line_cat) + len(line)  
                break  

        return start_idx, end_idx


if __name__ == "__main__":
    file_path = "example.pdf"
    parser = PDFParser(file_path)
    
    output_dir = "extracted_tables"
    table_extractor = PDFTableExtractor(output_dir)  

    if parser.is_scanned_pdf():
        print("The PDF is scanned.")
    else:
        print("The PDF contains text.")
    
    page_number = 12
    page_data = parser.parse_page_to_json(page_number, table_extractor)
    print(json.dumps(page_data, indent=4, ensure_ascii=False))
