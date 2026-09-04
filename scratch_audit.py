import sqlite3
import pandas as pd
import json

conn = sqlite3.connect("database/commerce.db")

print("--- QUERY 1 CATALOG ---")
df1 = pd.read_sql_query("SELECT product_id, name, attributes FROM products WHERE category LIKE '%smartphones%' AND price <= 30000", conn)
print(f"Smartphones under 30000: {len(df1)}")
for _, row in df1.iterrows():
    attrs = json.loads(row['attributes'])
    print(f" - {row['name']}: Processor={attrs.get('processor', 'N/A')}, Storage={attrs.get('storage_gb', 'N/A')}")

print("\n--- QUERY 2 CATALOG ---")
df2 = pd.read_sql_query("SELECT product_id, name, attributes FROM products WHERE category LIKE '%laptops%' AND price <= 80000", conn)
print(f"Laptops under 80000: {len(df2)}")
c_ram = 0
c_storage = 0
for _, row in df2.iterrows():
    attrs = json.loads(row['attributes'])
    ram = float(attrs.get('ram_gb', 0))
    storage = float(attrs.get('storage_gb', 0))
    print(f" - {row['name']}: RAM={ram}, Storage={storage}")
    if ram >= 16: c_ram += 1
    if storage >= 512: c_storage += 1
print(f"Laptops under 80000 with RAM>=16: {c_ram}")
print(f"Laptops under 80000 with Storage>=512: {c_storage}")

print("\n--- QUERY 3 CATALOG ---")
df3 = pd.read_sql_query("SELECT product_id, name, attributes FROM products WHERE category LIKE '%smartphones%' AND price <= 40000", conn)
print(f"Smartphones under 40000: {len(df3)}")
c_256 = 0
for _, row in df3.iterrows():
    attrs = json.loads(row['attributes'])
    storage = float(attrs.get('storage_gb', 0))
    camera = attrs.get('camera_mp', 'N/A')
    if storage == 256: c_256 += 1
    print(f" - {row['name']}: Storage={storage}, Camera={camera}")
print(f"Smartphones under 40000 with Storage==256: {c_256}")

conn.close()
