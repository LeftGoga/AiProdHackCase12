from langchain_community.document_loaders import TextLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json
from uuid import uuid1
from db_connector import db_connector
from langchain_chroma import Chroma
import os
class full_pipeline:
    def __init__(self,client,embed_fun=HuggingFaceEmbeddings(model_name = "cointegrated/rubert-tiny2")):
        self.embed_fun=embed_fun
        self.vectorstore = client.as_vector()

    def create_docs(self, data):
        '''
        Чанкует 1 страницу документа

        :param data: json страницы
        :return: список документов, созданых из чанка страницы
        '''

        text_splitter = SemanticChunker(self.embed_fun)
        texts = text_splitter.create_documents([data["raw_text"]])
        all_docs = []
        for i in range(len(texts)):
            doc = Document(page_content=texts[i].page_content,
                           metadata={"file_path": data["file_path"], "doc_type": data["doc_type"],
                                     "file_name": data["filename"], "page_number": data["page_number"]})
            all_docs.append(doc)
        return all_docs


    def storing(self,  docs):
        '''
        Сторит документы в векторсторе

        :param docs:
        :return:
        '''

        uuids = [str(uuid1()) for _ in range(len(docs))]
        self.vectorstore.add_documents(documents=docs, ids=uuids)

    def preprocess_single(self,json):

        '''
        Сторит 1 пдф в векторке
        :param json: джсон 1 документа
        :return:
        '''
        for i in range(len(json)):
            docs = self.create_docs(json[i])
            self.storing(docs)
    def preprocrss_multiple(self,list_of_json):
        """
        сторит множество доков
        :param list_of_json:
        :return:
        """
        for i in range(len(list_of_json)):
            self.preprocess_single(list_of_json[i])

    def as_retriever(self,k=1):
        return self.vectorstore.as_retriever(search_kwargs={"k": k})








if __name__ =="__main__":
    with open('parsed_output.json') as f:
        file = json.load(f)
        f.close()
    con = db_connector()
    con.create_db(db_path=os.getcwd() + "/DataBase")
    test = full_pipeline(con)

    test.preprocess_single(file)
    retr = test.as_retriever()
    print(retr.get_relevant_documents("арматурная сталь"))


