import sqlite3
conn = sqlite3.connect('vacancies_v2.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cursor.fetchall()])
cursor.execute("SELECT count(*) FROM favorites")
print("Favs:", cursor.fetchone()[0])
cursor.execute("SELECT count(*) FROM skipped_vacancies")
print("Skipped:", cursor.fetchone()[0])
