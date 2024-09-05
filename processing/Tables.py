import os
import fitz  
from PIL import Image as PILImage
import cv2
import numpy as np
from img2table.document import Image
import io

class PDFTableExtractor:
    """
    Класс для извлечения таблиц из PDF-документов и сохранения их в виде изображений.

    Атрибуты:
    ----------
    output_dir : str
        Директория для сохранения изображений с таблицами. Если папки нет, она будет создана.
    """

    def __init__(self, output_dir):
        """
        Инициализация класса PDFTableExtractor.

        Аргументы:
        ----------
        output_dir : str
            Путь к директории, в которой будут сохранены извлеченные таблицы. Если папки нет, она создается.
        """
        self.output_dir = output_dir
        
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def extract_tables_from_pdf(self, pdf_path):
        """
        Извлекает таблицы из PDF-документа, сохраняет их как изображения в заданную директорию.

        Аргументы:
        ----------
        pdf_path : str
            Путь к PDF-файлу, из которого необходимо извлечь таблицы.
        
        Описание процесса:
        ------------------
        1. Открывается PDF-документ.
        2. Каждая страница конвертируется в изображение.
        3. С помощью библиотеки img2table извлекаются таблицы.
        4. Для каждой найденной таблицы вычисляются координаты и таблица вырезается из изображения страницы.
        5. Извлеченные таблицы сохраняются в виде изображений в формате JPEG.
        """
        
        pdf_document = fitz.open(pdf_path)
        
        base_name = os.path.basename(pdf_path).rsplit('.', 1)[0]
        
        for page_num in range(len(pdf_document)):
            
            page = pdf_document.load_page(page_num)
            
            zoom_x = 2.0  
            zoom_y = 2.0  
            mat = fitz.Matrix(zoom_x, zoom_y)  
            pix = page.get_pixmap(matrix=mat)  
            img = PILImage.open(io.BytesIO(pix.tobytes()))  
            
            with io.BytesIO() as image_buffer:
                img.save(image_buffer, format="JPEG")
                image_buffer.seek(0)

                img_obj = Image(src=image_buffer)

                try:
                    extracted_tables = img_obj.extract_tables()
                
                    for table_index, table in enumerate(extracted_tables):

                        image_cv = np.array(img)

                        min_x = min(cell.bbox.x1 for row in table.content.values() for cell in row)
                        max_x = max(cell.bbox.x2 for row in table.content.values() for cell in row)
                        min_y = min(cell.bbox.y1 for row in table.content.values() for cell in row)
                        max_y = max(cell.bbox.y2 for row in table.content.values() for cell in row)

                        table_crop = image_cv[min_y:max_y, min_x:max_x]

                        output_filename = os.path.join(self.output_dir, f"{base_name}_page{page_num+1}_table{table_index+1}.jpg")
                        cv2.imwrite(output_filename, table_crop)
                        print(f"Table saved as {output_filename}")
                except:
                    pass

        pdf_document.close()


        
if __name__ == "__main__":
    output_dir = "extracted_tables"
    extractor = PDFTableExtractor(output_dir)
    extractor.extract_tables_from_pdf("test.pdf")
