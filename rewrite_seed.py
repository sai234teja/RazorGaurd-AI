import urllib3
import requests
import json
import os
urllib3.disable_warnings()
from catalog.seed_real_products import get_real_seed_products

products = get_real_seed_products()
headers = {'User-Agent': 'Mozilla/5.0'}

for p in products:
    if p['name'] == 'Moto G84':
        p['product_url'] = 'https://www.motorola.in/smartphones-moto-g84-5g/p'
        
    if p['category'] == 'smartphones':
        p['image_url'] = '/assets/images/demo_phone.jpg'
    elif p['category'] == 'laptops':
        p['image_url'] = '/assets/images/demo_laptop.jpg'
        
    if p.get('product_url') and not p['product_url'].startswith('/'):
        try:
            r = requests.get(p['product_url'], headers=headers, timeout=5, verify=False)
            if r.status_code >= 400:
                p['product_url'] = ''
        except:
            p['product_url'] = ''
            
    if p.get('image_url') and not p['image_url'].startswith('/'):
        try:
            r = requests.head(p['image_url'], headers=headers, timeout=5, verify=False)
            if r.status_code >= 400:
                r2 = requests.get(p['image_url'], headers=headers, timeout=5, verify=False)
                if r2.status_code >= 400:
                    p['image_url'] = ''
        except:
            p['image_url'] = ''

def format_product(p):
    return f"""        {{
            "product_id": {repr(p['product_id'])},
            "brand": {repr(p['brand'])},
            "name": {repr(p['name'])},
            "category": {repr(p['category'])},
            "price": {repr(p['price'])},
            "currency": {repr(p['currency'])},
            "description": {repr(p['description'])},
            "rating": {repr(p['rating'])},
            "stock": {repr(p['stock'])},
            "image_url": {repr(p['image_url'])},
            "product_url": {repr(p['product_url'])},
            "attributes": {repr(p['attributes'])},
            "use_cases": {repr(p['use_cases'])},
        }}"""

content = '''"""Verified public merchant catalog seed data for the AI commerce agent."""

from __future__ import annotations
from typing import Dict, List

def get_real_seed_products() -> List[Dict[str, object]]:
    return [
''' + ',\n'.join(format_product(p) for p in products) + '''
    ]
'''

with open('catalog/seed_real_products.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated seed_real_products.py successfully!')
