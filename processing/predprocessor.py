from processing.docx_predprocessor import DocParser
from processing.pdf_predprocessor import PDFProcessor
from processing.tables_predprocessor import PDFTableExtractor
import os
import json
import PyPDF2

class Preprocessor:
    def __init__(self):
        self.doc_parser = DocParser()
        self.pdf_processor = PDFProcessor()
        self.pdf_table_extractor = PDFTableExtractor()

    def process_file(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension in ['.doc', '.docx']:
            return self.doc_parser.parse(file_path)
        elif extension == '.pdf':

            page_count = self.get_pdf_page_count(file_path)
            # for page in range(page_count):
            pdf_parser = PDFProcessor()
            text = pdf_parser.process_pdf_page(file_path, 12)
            print(text)
            table_extractor = PDFTableExtractor()  
            tables_list = table_extractor.extract_tables_from_pdf(file_path, 12, combine_tables=True)
            """
            Тут вызов ламмы для самари таблицы
            """
            print(tables_list)

        else:
            raise ValueError(f"Unsupported file extension: {extension}")
        
    def get_pdf_page_count(self, file_path):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)