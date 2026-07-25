import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aleena",
    database="library_db"
)

cursor = db.cursor()