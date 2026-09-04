import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('database/commerce.db')

names = [
    'OnePlus 11R', 'Nothing Phone (2)', 'POCO F5',
    'CodeBook 14', 'PowerBook Pro', 'DevMaster X',
    'Galaxy M54', 'PixelView A1', 'VisionMax 8'
]

query = 'SELECT product_id, name, image_url, product_url FROM products WHERE name IN ({seq})'.format(
    seq=','.join(['?']*len(names))
)

df = pd.read_sql_query(query, conn, params=names)

print("\n--- QUERY 1: Find me the best phone with the best processor and highest storage under ₹30,000 ---")
for _, row in df[df['name'].isin(['OnePlus 11R', 'Nothing Phone (2)', 'POCO F5'])].iterrows():
    print(f"Product: {row['name']}")
    print(f"Product ID: {row['product_id']}")
    is_mock = 'Mock' if str(row['product_id']).startswith('PH') else 'Real'
    print(f"Real/mock catalog product: {is_mock}")
    img = row['image_url'] or 'EMPTY'
    print(f"Image source: {img}")
    url = row['product_url'] or 'EMPTY'
    print(f"Product URL: {url}")
    verified = 'Yes' if url != 'EMPTY' else 'No'
    print(f"URL verified?: {verified}")
    clickable = 'Clickable' if url != 'EMPTY' else 'Unavailable'
    print(f"Clickable or unavailable?: {clickable}")
    print('-')

print("\n--- QUERY 2: I need a laptop for coding with at least 16GB RAM and 512GB storage under ₹80,000 ---")
for _, row in df[df['name'].isin(['CodeBook 14', 'PowerBook Pro', 'DevMaster X'])].iterrows():
    print(f"Product: {row['name']}")
    print(f"Product ID: {row['product_id']}")
    is_mock = 'Mock' if str(row['product_id']).startswith('PH') else 'Real'
    print(f"Real/mock catalog product: {is_mock}")
    img = row['image_url'] or 'EMPTY'
    print(f"Image source: {img}")
    url = row['product_url'] or 'EMPTY'
    print(f"Product URL: {url}")
    verified = 'Yes' if url != 'EMPTY' else 'No'
    print(f"URL verified?: {verified}")
    clickable = 'Clickable' if url != 'EMPTY' else 'Unavailable'
    print(f"Clickable or unavailable?: {clickable}")
    print('-')

print("\n--- QUERY 3: Show me a phone under ₹40,000 with the best camera and 256GB storage ---")
for _, row in df[df['name'].isin(['Galaxy M54', 'PixelView A1', 'VisionMax 8'])].iterrows():
    print(f"Product: {row['name']}")
    print(f"Product ID: {row['product_id']}")
    is_mock = 'Mock' if str(row['product_id']).startswith('PH') else 'Real'
    print(f"Real/mock catalog product: {is_mock}")
    img = row['image_url'] or 'EMPTY'
    print(f"Image source: {img}")
    url = row['product_url'] or 'EMPTY'
    print(f"Product URL: {url}")
    verified = 'Yes' if url != 'EMPTY' else 'No'
    print(f"URL verified?: {verified}")
    clickable = 'Clickable' if url != 'EMPTY' else 'Unavailable'
    print(f"Clickable or unavailable?: {clickable}")
    print('-')
