import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""  # Par défaut vide sur WAMP/XAMPP
        self.database = "gestion_budget"

    def connecter(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if conn.is_connected():
                return conn
        except Error as e:
            print(f"Erreur lors de la connexion à MySQL: {e}")
            return None