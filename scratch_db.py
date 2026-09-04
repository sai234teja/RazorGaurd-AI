import sqlite3
import pandas as pd

conn = sqlite3.connect("database/commerce.db")
df = pd.read_sql_query("SELECT product_id, name, category, price FROM products WHERE category LIKE '%laptop%'", conn)
print("Laptops:")
print(df)
conn.close()
