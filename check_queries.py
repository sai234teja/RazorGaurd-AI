import requests
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

queries = [
    'Find me the best phone with the best processor and highest storage under ₹30,000',
    'I need a laptop for coding with at least 16GB RAM and 512GB storage under ₹80,000',
    'Show me a phone under ₹40,000 with the best camera and 256GB storage'
]

for i, q in enumerate(queries):
    print(f'\n--- QUERY {i+1}: {q} ---')
    payload = {'message': q}
    try:
        r = requests.post('http://127.0.0.1:5000/api/recommend/stream', json=payload, stream=True)
        for line in r.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'results':
                        products = data.get('products', [])
                        for p in products:
                            print(f"Product: {p.get('name')}")
                            print(f"Product ID: {p.get('product_id')}")
                            is_mock = 'Mock' if str(p.get('product_id')).startswith('PH') else 'Real'
                            print(f"Real/mock catalog product: {is_mock}")
                            print(f"Image source: {p.get('image_url') or 'EMPTY'}")
                            url = p.get('product_url') or 'EMPTY'
                            print(f"Product URL: {url}")
                            print(f"URL verified?: {'Yes' if url != 'EMPTY' else 'No'}")
                            print(f"Clickable or unavailable?: {'Clickable' if url != 'EMPTY' else 'Unavailable'}")
                            print('-')
                        break
    except Exception as e:
        print('Error:', e)
