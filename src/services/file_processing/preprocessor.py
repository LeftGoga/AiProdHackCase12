from src.services.file_processing.doc import DocProcessor
from src.services.file_processing.pdf import PDFProcessor
from src.processing.tables_predprocessor import PDFTableExtractor
from src.services.llm_models.multimodal_llamma_cpm import MultimodalLlammaCPM
import os
import PyPDF2
import re
import datetime


class Preprocessor:
    def __init__(self, rag_pp):
        self.doc_processor = DocProcessor()
        self.pdf_processor = PDFProcessor()
        self.pdf_table_extractor = PDFTableExtractor()
        self.llama_cpm = MultimodalLlammaCPM()
        self.rag_pp = rag_pp

    def process_file(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension in [".doc", ".docx"]:
            return self.doc_processor.parse(file_path)
        elif extension == ".pdf":
            log_file_path = "./processing_log.txt"

            page_count = self.get_pdf_page_count(file_path)

            flag_continued_table = False
            for page in range(0, page_count):
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"{current_time} - Страница {page + 1} из {page_count} ---- {file_path}\n"
                    )
                print(f"Страница {page + 1} из {page_count} ---- {file_path}")
                pdf_parser = PDFProcessor()
                text = pdf_parser.process_pdf_page(file_path, page + 1, page_count)
                table_extractor = PDFTableExtractor()
                tables_list = table_extractor.extract_tables_from_pdf(
                    file_path, page + 1, page_count, combine_tables=True
                )
                for i in range(len(tables_list)):
                    image_to_summary = []
                    for j in range(len(tables_list[i]["page_coords"])):
                        if flag_continued_table:
                            flag_continued_table = False
                            continue

                        image_to_summary += [
                            table_extractor.extract_table_image(
                                file_path,
                                page + 1 + j,
                                tables_list[i]["page_coords"][j],
                            )
                        ]

                    temp_promt = table_extractor.extract_table_text(
                        file_path, page + 1, page_count
                    )[i]
                    promt = temp_promt[0 : len(temp_promt) // 2]

                    if len(image_to_summary) != 0:
                        pass
                        summary = self.llama_cpm.generate_summary(
                            image_to_summary, promt
                        )
                        tables_list[i]["raw_text"] = summary

                        ###################################################
                        self.rag_pp.preprocess_page(tables_list[i])
                        # print(tables_list[i])
                        # ЭТО ЭМБЕДИМ это таблица из списка таблиц на странице
                        #####################################################

                    if (
                        i == len(tables_list) - 1
                        and len(tables_list[i]["page_coords"]) > 1
                    ):
                        flag_continued_table = True

                ###################################################
                self.rag_pp.preprocess_page(text)
                # print(text)
                # ЭТО ЭМБЕДИМ это текст
                #####################################################
                # print()

        else:
            raise ValueError(f"Unsupported file extension: {extension}")

    def clean_text(self, text: str) -> str:
        text = re.sub(r"(?<=\S)-\n(?=\S)", "", text)

        text = re.sub(r"(\s)П(\s)", r"\1II\2", text)
        text = re.sub(r"(\s)П,", r"\1II,", text)
        text = re.sub(r",П(\s)", r",II\1", text)
        text = re.sub(r"(\s)Ш(\s)", r"\1III\2", text)
        text = re.sub(r"(\s)Ш,", r"\1III,", text)
        text = re.sub(r",Ш(\s)", r",III\1", text)

        text = re.sub(r"\n", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\bTig\b|[\x0c]", "", text)
        text = re.sub(r"\|", "", text)
        text = re.sub(r"-ro", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def get_pdf_page_count(self, file_path):
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
