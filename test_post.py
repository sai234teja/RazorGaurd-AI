import requests

print("\nTesting /api/recommend GET (might be POST or different module)...")
r1 = requests.post('http://127.0.0.1:5000/api/recommend', json={'q': 'phone'})
print(f"POST /api/recommend Status: {r1.status_code}")

r2 = requests.post('http://127.0.0.1:5000/api/recommend/stream', json={'q': 'phone'})
print(f"POST /api/recommend/stream Status: {r2.status_code}")
