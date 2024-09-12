
from models.multimodal_llamma_cpm import MultimodalLlammaCPM
from models.LLM_interaction import llm
from pdf2image import convert_from_path
import time
import transformers
from processing.predprocessor import Preprocessor
from processing.rag_pipeline import full_pipeline


class Inference:
    def __init__(self,db_path="/home/aiproducttest/AiProdHackCase12-1_Copy/AiProdHackCase12-1/database/db",k=2):
        self.multimodal = MultimodalLlammaCPM()
        self.con = db_connector()
        self.con.create_db(db_path)
        self.retr = self.con.as_retr(k)
        self.llm = llm(self.retr)
        transformers.set_seed(42)

    

    def answer(self, q):
        ret_doc = self.retr.get_relevant_documents(q)

        imgs=[]
        page_doc = {"Doc":[], "Page":[]}
        prompts=''
        for i,item in enumerate(ret_doc):
            if item.metadata["doc_type"]=="table":
                page_doc['Doc'].append(item.metadata["file_name"])
                page_doc['Page'].append(item.metadata["page_number"])
                imgs.append((item.metadata["page_number"],item.metadata["file_name"]))
            else:
                page_doc['Doc'].append(item.metadata["file_name"])
                page_doc['Page'].append(item.metadata["page_number"])
                prompts+="\n\n"+item.page_content
        if imgs:
            print("multimodal")
            images = self.get_imgs_pathes(imgs)
            ans = self.multimodal.answer(images, q)+ "\n" +"Откуда взято: "+"\n"+ str(page_doc['Doc'])+"\n"+ str(page_doc['Page'])

            
        else:
            print("simple llm")
            ans = self.llm.chat(q) + "\n" +"Откуда взято: "+"\n"+ str(page_doc['Doc'])+"\n"+ str(page_doc['Page'])
        return  ans   



    def get_imgs_pathes(self, imgs):
        img_pathes=[]
        for i in imgs:

            path_doc = f"/home/aiproducttest/AiProdHackCase12-1_Copy/AiProdHackCase12-1/data/documents/{i[1]}.pdf"
           
            page = convert_from_path(path_doc,first_page=i[0],last_page=i[0],dpi=300)

            img_pathes.append(page[0])
   
        return img_pathes
    
    def add_to_db(self,file_path):

        test = full_pipeline(self.con)
        prep = Preprocessor(test)
        prep.process_file(file_path)

        print("Документ добавлен")
    



if __name__ =="__main__":
    
    from database.db_connector import db_connector

    start = time.time()
    inf = Inference(k=3)
    print(inf.answer("Какие классы арматурной стали существуют?"))
    end = time.time()
    print("elapsed_time: ", end-start)