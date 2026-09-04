import sqlite3
import pandas as pd

conn = sqlite3.connect('database/commerce.db')

def print_category(cat):
    print(f'--- {cat} ---')
    df = pd.read_sql_query(f"SELECT * FROM products WHERE category LIKE '%{cat}%'", conn)
    for _, row in df.iterrows():
        print(f"ID: {row['product_id']} | {row['name']} | Price: {row['price']} | URL: {row['product_url']} | Img: {row['image_url']}")
        print(f"  Attrs: {row['attributes']}")

print_category('phone')
print_category('laptop')
