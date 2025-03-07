from dotenv import load_dotenv
import os
import psycopg2

load_dotenv(dotenv_path=".env")
# print(os.getenv("DBNAME"))
# print(os.getenv("USER"))
# print(os.getenv("ACCESS"))
# print(os.getenv("HOST"))
# print(os.getenv("PORT"))

class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DBNAME"),
            user=os.getenv("USER"),
            password=os.getenv("ACCESS"),
            host=os.getenv("HOST"),
            port=os.getenv("PORT"),
        )
        self.conn.autocommit = True

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.close()

PsqlDB = DatabaseConnection()