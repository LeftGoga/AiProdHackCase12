import logging

import transformers

from src.core.config import TranslatorConfig
from src.core.database import Database
from pdf2image import convert_from_path

from src.core.dto import Prompt
from src.services.llm_models.interaction import LLMInteraction
from src.services.llm_models.multimodal_llamma_cpm import MultimodalLlammaCPM
from src.services.file_processing.preprocessor import Preprocessor
from src.services.file_processing.rag_pipeline import RAGPipeline


class AIService:
    def __init__(
        self,
        translator_config: TranslatorConfig,
        db_path="/home/aiproducttest/AiProdHackCase12/db",
        k=2,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.translator_config = translator_config
        self.multimodal = MultimodalLlammaCPM(translator_config)
        self.con = Database()
        self.con.create_db(db_path)
        self.retr = self.con.as_retr(k)
        self.llm = LLMInteraction(self.retr)
        transformers.set_seed(42)

    def process_message(self, prompt: Prompt) -> str:
        self.add_to_db(prompt.file_paths)
        return self.answer(prompt.text)

    def answer(self, q):
        ret_doc = self.retr.get_relevant_documents(q)

        imgs = []
        page_doc = {"Doc": [], "Page": []}
        prompts = ""
        for i, item in enumerate(ret_doc):
            page_doc["Doc"].append(str(item.metadata["file_name"]))
            page_doc["Page"].append(str(item.metadata["page_number"]))
            if item.metadata["doc_type"] == "table":
                imgs.append((item.metadata["page_number"], item.metadata["file_name"]))
            else:
                prompts += "\n\n" + item.page_content

        if imgs:
            self.logger.info("multimodal")
            images = self.get_imgs_pathes(imgs)
            text = self.multimodal.answer(images, q)
        else:
            self.logger.info("simple llm")
            text = self.llm.chat(q)
        ans = (
            text
            + "<br><br>"
            + "Откуда взято: "
            + "<br>"
            + ", ".join(
                [f"{d} (Стр. {p})" for d, p in zip(page_doc["Doc"], page_doc["Page"])]
            )
        )

        return ans

    @staticmethod
    def get_imgs_pathes(imgs):
        img_pathes = []
        for i in imgs:
            path_doc = f"/home/aiproducttest/AiProdHackCase12/data/documents/{i[1]}.pdf"

            page = convert_from_path(path_doc, first_page=i[0], last_page=i[0], dpi=300)

            img_pathes.append(page[0])

        return img_pathes

    def add_to_db(self, file_paths: list[str]):
        test = RAGPipeline(self.con)
        prep = Preprocessor(test, self.translator_config)
        for file_path in file_paths:
            prep.process_file(file_path)

        self.logger.info("Документ добавлен")
