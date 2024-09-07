from processing.docx_predprocessor import DocParser
from processing.pdf_predprocessor import PDFProcessor
from processing.tables_predprocessor import PDFTableExtractor
import os
import json

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
            pdf_parser = PDFProcessor()
            pdf_parser.process_pdf_page(file_path, 12)
            
            table_extractor = PDFTableExtractor()  
            table_extractor.extract_tables_on_page()
            print(json.dumps(page_data, indent=4, ensure_ascii=False))

        else:
            raise ValueError(f"Unsupported file extension: {extension}")
        
