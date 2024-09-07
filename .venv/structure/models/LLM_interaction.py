import langchain
import torch
from PIL import Image

from transformers import AutoModel, AutoTokenizer

class llm:
    def __init__(self,model_dir, promt):
        self.model = AutoModel.from_pretrained(model_dir, trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
        self.promt = promt
    def chat(self, image,msgs,temp = 0.0001,sampling =True):
        res = self.model.chat(
            image=image,
            msgs=msgs,
            tokenizer=self.tokenizer,
            sampling=sampling,  # if sampling=False, beam_search will be used by default
            temperature=temp,
            system_prompt=self.promt # pass system_prompt if needed
        )
        return res
