import urllib3
import requests
from catalog.seed_real_products import get_real_seed_products
import sys

urllib3.disable_warnings()

products = get_real_seed_products()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

results = []
for p in products:
    url = p.get('product_url', '')
    if p['name'] == 'Moto G84':
        url = 'https://www.motorola.in/smartphones-moto-g84-5g/p'
        p['product_url'] = url
        
    if not url:
        results.append({'id': p['product_id'], 'name': p['name'], 'url': '', 'status': 'EMPTY'})
        continue
        
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False, allow_redirects=True)
        # Verify it doesn't contain obvious 404 indicators in the title or text
        # But we must be careful not to false positive
        if r.status_code >= 400:
            results.append({'id': p['product_id'], 'name': p['name'], 'url': url, 'status': f'FAILED ({r.status_code})'})
        elif '<title>Page Not Found' in r.text or '<title>404' in r.text or 'Sorry, we couldn\'t find that page' in r.text:
            results.append({'id': p['product_id'], 'name': p['name'], 'url': url, 'status': f'FAILED (404 Page)'})
        else:
            results.append({'id': p['product_id'], 'name': p['name'], 'url': url, 'status': 'OK'})
    except Exception as e:
        results.append({'id': p['product_id'], 'name': p['name'], 'url': url, 'status': f'ERROR ({str(e)[:20]})'})

for r in results:
    print(f"{r['id']} | {r['name']} | {r['status']} | {r['url']}")
