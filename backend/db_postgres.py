import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="library",
    user="postgres",
    password="1904"
)

def get_cursor():
    return conn.cursor()
