import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
from models.llm_translator import YandexTranslate

class MultimodalLlammaCPM:
    def __init__(self, model_name = 'openbmb/MiniCPM-V-2_6'):
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True,
            attn_implementation='sdpa', torch_dtype=torch.bfloat16)
        self.model = self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.question = """You need an unambiguous detailed description of the table contents to upload to the database in the Table Data Description column. Pay attention to the column names and row names!!! 
    HERE THE MAIN PART: Give answer in english. Do not translate to english Russian terms!!!"""

        self.ruen_translator = YandexTranslate(target_language='en')
        self.enru_translator = YandexTranslate(target_language='ru')


    def generate_summary(self, image_paths, promt = ''):
        # Load the image
        images = [img.convert('RGB') for img in image_paths]
        print()
        print("Вызов модельки")
        msgs = [{'role': 'user', 'content': images + ["Question: " + self.question +"context: "+ promt]}]

        # Generate response
        res = self.model.chat(
            image=None,
            msgs=msgs,
            tokenizer=self.tokenizer,
            max_new_tokens=300
        )

        translated_response = self.enru_translator.translate(res)
        return translated_response
        # return res


    def answer(self,image_paths,question,add_context=''):
        images = [img.convert('RGB') for img in image_paths]
        system =         """You are an expert in construction documentation. You will be given a user's question and images that have tables on them.
        First, try to find tables on image and look for answer in them.Your task is to answer the user's question 
                    using information from the images. Be attentive to the details: The name of the columns of the table, the decimal separator. 
        Follow the following rules:
        1. If you can't find the answer to the question, don't try to come up with it. Just write "There is no information"
        2. If you have found the answer, then be brief, fit into 5 sentences."""


        q=self.ruen_translator.translate(question)
        #pr = self.ruen_translator.translate(add_context)
        msgs = [{'role': 'user', 'content': images + ["context: "+ add_context+"question: " +q]}]

        # Generate response
        res = self.model.chat(
            image=None,
            msgs=msgs,
            tokenizer=self.tokenizer,
            max_new_tokens=300,
            system_promt = system
        )

        translated_response = self.enru_translator.translate(res)
        return translated_response 