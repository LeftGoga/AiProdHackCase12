import langchain
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
from langchain.prompts import PromptTemplate
from transformers import AutoModel, AutoTokenizer
from langchain.prompts import PromptTemplate
from transformers import BitsAndBytesConfig
from transformers import AutoModelForCausalLM
from transformers import pipeline
from langchain_huggingface.llms import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough




class multimodal_llm_inter:

    '''
    Мультимодалка
    '''
    def __init__(self,model_dir):
        self.model = AutoModel.from_pretrained(model_dir, trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)

    def chat(self, question,prompt,images = None,temp = 0.1,sampling =True):
        img_lst = []
        if images:
            for i in images:
                image = Image.open(i).convert('RGB')
                img_lst.append(image)
            msgs = [{'role': 'user', 'content': [*img_lst, question]}]
        else:
            msgs = [{'role': 'user', 'content': [question]}]

        res = self.model.chat(
            image=None,
            msgs=msgs,
            tokenizer=self.tokenizer,
            sampling=sampling,  # if sampling=False, beam_search will be used by default
            temperature=temp,
            system_prompt=prompt # pass system_prompt if needed
        )
        return res


class llm_inter:

    '''
    Обычная ллм
    '''
    def __init__(self, model_name, retr):
        self.retr = retr
        self.chain = (
                {
                    "context": self.retr | self.format_docs,
                    "question": RunnablePassthrough(),
                }
                | self.default_prompt()
                | self.create_pipeline(model_name)
                | StrOutputParser()
        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def chat(self, query):
        ans = self.chain.invoke(query)

        return ans.replace("\n\n", "").replace(" Нет информации.", "")

    def get_meta(self,q):
        docs = self.retr.get_relevant_documents(q)
        metadata = []
        for i in docs:
            metadata.append(i.metadata)
        return metadata
    def create_pipeline(self, model_name):

        model = AutoModelForCausalLM.from_pretrained(model_name, low_cpu_mem_usage= True)
        tokenizer = AutoTokenizer.from_pretrained(model_name, low_cpu_mem_usage=True)



        pipe = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512, return_full_text=False
        )
        hf = HuggingFacePipeline(
            pipeline=pipe
        )
        return hf

    def default_prompt(self):
        prompt_template = """Ты - эксперт по нормативной документации. Используя контекст, предложенный далее, ответь на вопрос и один ответ в конце. Придерживайся следующих правил:
        1. Если не найдешь ответа, не пытайся придумать ответ. Просто напиши "Нет информации" 
        2. Если вы нашли ответ, запишите его кратко
        3. Не пиши лишней информации после ответа


        {context}

        Вопрос: {question}

        Ответ:
        """

        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        return prompt