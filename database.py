import pymysql

class Database:
    def __init__(self,host,port,user,password,database):
        self.connection = pymysql.connect(
            host = host,
            port = port,
            user = user,
            password = password,
            database = database
            )
            self.cursor = self.connection.cursor()
            
            def execute_query(self, query, params= None ):
                try:
                    self.cursor.execute(query, params)
                    self.connection.commit()
                    return self.cursor.fetchall()
                
                except Exception ase:
                    print(f"An error occured: {e}")
                    self.connection.rollback()
                    
                    
            def insert(self, query, params):
                #query = "IINSERT INTO orders (item_name, item_proce "
                #params =(items.name )
                
                
                
                
                
                
                