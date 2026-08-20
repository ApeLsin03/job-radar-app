import sqlite3
conn = sqlite3.connect('vacancies_v2.db')
c = conn.cursor()
c.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in c.fetchall():
    print(row[0])
