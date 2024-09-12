import os
import fitz  
from PIL import Image as PILImage
import numpy as np
from img2table.document import Image
import io
import pytesseract
import re

class PDFTableExtractor:

    def __init__(self, output_dir = ''):
        self.output_dir = output_dir
        
    def extract_tables_from_pdf(self, pdf_path, page_num, page_count, combine_tables=False):
        page_num = page_num-1
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(page_num)
        page_height = page.rect.height
        
        tables_json = self.extract_tables_on_page(pdf_document, pdf_path, page_num)
        # print(page_num, page_count-1)
        if(page_num==page_count-1):
            pdf_document.close()
            # print(tables_json)
            return tables_json

        next_page = pdf_document.load_page(page_num+1)
        next_page_height = next_page.rect.height
        
        if combine_tables and page_num < len(pdf_document) - 1 and tables_json:
            next_page_tables_json = self.extract_tables_on_page(pdf_document, pdf_path, page_num + 1)
            if next_page_tables_json:
                for current_table in tables_json:
                    for next_table in next_page_tables_json:
                        if self.is_table_continued(current_table, next_table, page_height, next_page_height):
                            current_table['page_coords'].extend(next_table['page_coords'])

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
                
                for table in extracted_tables:
                    
                    min_x = min(cell.bbox.x1 for row in table.content.values() for cell in row)
                    max_x = max(cell.bbox.x2 for row in table.content.values() for cell in row)
                    min_y = min(cell.bbox.y1 for row in table.content.values() for cell in row)
                    max_y = max(cell.bbox.y2 for row in table.content.values() for cell in row)

                    coordinates = [(min_x, min_y, max_x, max_y)]

                    result.append({
                        "file_path": pdf_path,
                        "filename": base_name,
                        "doc_type": "table",
                        "page_number": page_num+1,
                        "page_coords": coordinates
                    })

            except Exception as e:
                print(f"Ошибка при извлечении таблицы: {str(e)}")

        return result

    def is_table_continued(self, current_table, next_table, page_height, next_page_height):
        """Проверяет, продолжается ли таблица на следующей странице"""
        current_coords = current_table['page_coords'][-1]
        next_coords = next_table['page_coords'][0]
        
        current_max_y = current_coords[3]//2
        next_min_y = next_coords[1]//2

        # print(current_max_y,">", 0.8 * page_height)
        # print( next_min_y, "<", 0.2 * next_page_height)
        # print(page_height, next_page_height)
        # print(current_max_y >= 0.8 * page_height and next_min_y <= 0.2 * next_page_height)
        
        if current_max_y >= 0.8 * page_height and next_min_y <= 0.2 * next_page_height:
            return True
        return False

    def extract_table_image(self, pdf_path, page_num, coordinates):
        page_num=page_num-1
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(page_num)
        
        zoom_x = 2.0
        zoom_y = 2.0
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        img = PILImage.open(io.BytesIO(pix.tobytes()))
        
        image_cv = np.array(img)
        min_x, min_y, max_x, max_y = coordinates
        table_crop = image_cv[min_y:max_y, min_x:max_x]
        
        table_image = PILImage.fromarray(table_crop)
        pdf_document.close()

        return table_image

        

    def extract_table_text(self, pdf_path, page_num, page_count):
        """Метод для извлечения текста таблицы с помощью OCR"""
        tables_json = self.extract_tables_from_pdf(pdf_path, page_num, page_count)
        if not tables_json:
            return "Таблицы не найдены на указанной странице."
        tables_text_list = []
        for i in range(len(tables_json)):
            coordinates = tables_json[i]["page_coords"]
            table_image = self.extract_table_image(pdf_path, page_num, coordinates[0])
            
            ocr_text = pytesseract.image_to_string(table_image, lang='rus+eng')

            tables_text_list+=[self.clean_text(ocr_text)]
        return tables_text_list.copy()
    
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