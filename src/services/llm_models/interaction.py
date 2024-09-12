from transformers import AutoTokenizer
from langchain.prompts import PromptTemplate
from transformers import AutoModelForCausalLM
from transformers import pipeline
from langchain_huggingface.llms import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class LLMInteraction:
    def __init__(self, retr, model_name="AnatoliiPotapov/T-lite-instruct-0.1"):
        self.chain = (
            {
                "context": retr | self.format_docs,
                "question": RunnablePassthrough(),
            }
            | self.default_prompt()
            | self.create_pipeline(model_name)
            | StrOutputParser()
        )

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def chat(self, query):
        ans = self.chain.invoke(query)

        index = ans.find("Вопрос:")
        if index != -1:
            ans_cut = ans[:index + len("Вопрос:")]
            return ans_cut.replace("Вопрос:","")
        else:
            return ans.replace("Вопрос:","" )
    
    @staticmethod
    def create_pipeline(model_name):
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        model = AutoModelForCausalLM.from_pretrained(model_name)

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=256,
            return_full_text=False,
            do_sample=True,
            temperature=0.1,
        )
        hf = HuggingFacePipeline(pipeline=pipe)
        return hf

    @staticmethod
    def default_prompt():
        prompt_template = """Ты - эксперт по нормативной документации. Используя контекст, предложенный далее, ответь на вопрос и один ответ в конце. Придерживайся следующих правил:
        1. Если не найдешь ответа, не пытайся придумать ответ. 
        2. Если вы нашли ответ, запишите его кратко
        3. Если ответила на вопрос пользователя - прекращай свою работу. 


        {context}

        Вопрос: {question}

        Ответ:
        """

        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        return prompt
