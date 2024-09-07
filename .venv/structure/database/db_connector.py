import chromadb as cdb
import os.path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
class db_connector:
        '''
              Базовый коннектор векторки, создание самой бд, коллекций, запросы по добавлению, удалению, текстовый запрос
        '''

        def __init__(self):

                self.client = None
                self.coll = None
                self.coll_list = []
                self.embed_fun = HuggingFaceEmbeddings(model_name = "cointegrated/rubert-tiny2")
        def create_db(self,db_path):

                self.client = cdb.PersistentClient(path = db_path,settings = cdb.config.Settings(allow_reset=True)
                                                  )
                self.reset_db()


        def set_coll(self,name):
                self.coll = create_or_get(name)

        def create_or_get(self,name):
                if self.embed_fun:
                        self.coll = self.client.get_or_create_collection(name = name,embedding_function=embedding_function)
                else:
                        self.coll = self.client.get_or_create_collection(name=name)
                self.coll_list.append(name)

        def add_to_coll(self,docs,metadatas,ids,coll_name=None):
                if coll_name:
                        self.set_coll(coll_name)
                self.coll.add(documents = docs,metadatas= metadatas,ids = ids)

        def remove(self, doc_ids, coll_name=None):
                if coll_name:
                        self.set_coll(coll_name)
                self.coll.delete(doc_ids)

        def update_doc(self,doc_id,new_docs, coll_name=None):
                if coll_name:
                        self.set_coll(coll_name)
                self.coll.update(ids=doc_ids,documents = new_docs)


        def query_text(self, query,n_res = 1,coll_name=None):
                if coll_name:
                        self.set_coll(coll_name)
                return self.coll.query(query_texts =query,n_results = n_res)

        def reset_db(self):
                self.client.reset()
        def as_vector(self):
                if self.embed_fun:
                        vector = Chroma(
                                client=self.client,
                                collection_name="docs",
                                embedding_function= self.embed_fun
                        )
                else:
                        vector = Chroma(
                                client=self.client,
                                collection_name="docs"
                        )

                return vector
