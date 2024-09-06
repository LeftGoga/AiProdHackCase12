import os
import fitz  
from PIL import Image as PILImage
import numpy as np
from img2table.document import Image
import io
import pytesseract

class PDFTableExtractor:

    def __init__(self, output_dir):
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

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
        
        coordinates = tables_json[0]["координаты таблицы"]
        table_image = self.extract_table_image(pdf_path, page_num, coordinates)
        
        ocr_text = pytesseract.image_to_string(table_image, lang='rus+eng')
        return ocr_text

if __name__ == "__main__":
    output_dir = "extracted_tables"
    extractor = PDFTableExtractor(output_dir)
    
    pdf_path = "test3.pdf"
    page_num = 7
    tables_json = extractor.extract_tables_from_pdf(pdf_path, page_num, combine_tables=True)
    print(tables_json)
    
    if tables_json:
        coordinates = tables_json[0]["координаты таблицы"]
        table_image = extractor.extract_table_image(pdf_path, page_num, coordinates)
        table_image.show()  

    ocr_text = extractor.extract_table_text(pdf_path, page_num)
    print(ocr_text)
