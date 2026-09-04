import sqlite3
import re

with open('catalog/seed_real_products.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"https://www.motorola.in/smartphones-moto-g84-5g/p"', '""')

with open('catalog/seed_real_products.py', 'w', encoding='utf-8') as f:
    f.write(content)

conn = sqlite3.connect('database/commerce.db')
c = conn.cursor()
c.execute("UPDATE products SET product_url = '' WHERE product_id = 'REAL_SMART_008'")
conn.commit()

print('Cleared Moto G84 URL in seed and DB!')
