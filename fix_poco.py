import sqlite3
import re

with open('catalog/seed_real_products.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"https://www.mi.com/in/product/poco-f5/"', '""')

with open('catalog/seed_real_products.py', 'w', encoding='utf-8') as f:
    f.write(content)

conn = sqlite3.connect('database/commerce.db')
c = conn.cursor()
c.execute("UPDATE products SET product_url = '' WHERE product_id = 'REAL_SMART_006'")
conn.commit()

print('Cleared POCO F5 URL in seed and DB!')
