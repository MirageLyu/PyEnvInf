import sqlite3
import os

class DBUtils:
    def __init__(self, dbPath):
        if os.path.exists(dbPath):
            self.conn = sqlite3.connect(dbPath)
        else:
            self.conn = sqlite3.connect(dbPath)
            self.createUrlTable()
        print("Opened database successfully")
        
    def getConn(self):
        return self.conn
    
    # only call once, never use later
    def createUrlTable(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE FILEURLS
                  (ID INT PRIMARY KEY NOT NULL,
                  FNAME VARCHAR(200) NOT NULL,
                  REMOTEPATH VARCHAR(200) NOT NULL,
                  FTYPE VARCHAR(20) NOT NULL);''')
        print("Table created successfully")
        c.close()
        self.conn.commit()
    
    def closeConn(self):
        print("Connection disconnected...")
        self.conn.close()
        self.conn = None
        
    def insertToUrlTable(self, id, fname, remotepath, ftype):
        assert(self.conn != None)
        c = self.conn.cursor()
        c.execute('''INSERT INTO FILEURLS (ID, FNAME, REMOTEPATH, FTYPE) \
                  VALUES (?, ?, ?, ?)''', (id, fname, remotepath, ftype))
        c.close()
        self.conn.commit()
        
    def __del__(self):
        if self.conn != None:
            self.closeConn()
    
    def getRemotePathByID(self, id):
        assert(self.conn != None)
        c = self.conn.cursor()
        results = c.execute("SELECT REMOTEPATH FROM FILEURLS WHERE ID=" + str(id))
        # assert(len(results) != 1)
        return results.fetchall()[0][0]
        

# dbutils = DBUtils('url.db')
# dbutils.createUrlTable()