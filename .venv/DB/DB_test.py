from db_connector import db_connector
import os
con = db_connector()
con.create_db(db_path = os.getcwd()+"/DataBase")
con.create_or_get("test")
con.add_to_coll([ "This is a document about pineapple","This is a document about oranges"],[{"dat1":"1"},{"dat2":"2"}],["id1","id2"])
print(con.coll.get())
print(con.query_text(["This is a query document about hawaii"]))