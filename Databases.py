from mysql import connector

class Databases:

    def __init__(self, host, port, user, password, database, table):
        try:
            self.con = connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
            self.connection = self.con
            self.cursor = self.con.cursor()
        except:
            self.cursor = None
            self.connection = None
        self.table = table

    def getAllId(self):
        '''
        获取数据库现有的所有(番剧页面）的id
        Returns: int []
           数据库所有（番剧页面）的id
        -------

        '''
        if self.cursor == None:
            return []
        self.cursor.execute(f"SELECT Bangumi页面 FROM {self.table} ORDER BY Bangumi页面 ASC")
        result = self.cursor.fetchall()
        dbId = [i[0] for i in result]
        return dbId

    def deleteById(self, id):
        if self.cursor == None:
            return False;
        try:
            self.cursor.execute(f"DELETE FROM {self.table} WHERE Bangumi页面={id}")
            self.connection.commit()
        except:
            return False
        return True

if __name__ == "__main__":
    db1 = Databases(host="localhost", port="3307", user="WIIASD", password="987654321", database="myanime")
    db1.connect()
    print(db1.cursor)