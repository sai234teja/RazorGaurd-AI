import requests

def test_endpoints():
    print("Testing B2A manifest...")
    r = requests.get('http://127.0.0.1:5000/.well-known/agentic-commerce.json')
    print(f"B2A Manifest Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Manifest loaded successfully.")
        print(f"Gated financial endpoint: {data.get('endpoints', {}).get('checkout_prepare', {}).get('security')}")
    else:
        print("Failed to load manifest.")

    print("\nTesting /api/recommend...")
    r = requests.get('http://127.0.0.1:5000/api/recommend', params={'q': 'phone'})
    print(f"/api/recommend Status: {r.status_code}")

    print("\nTesting /api/orders...")
    r = requests.get('http://127.0.0.1:5000/api/orders')
    print(f"/api/orders Status: {r.status_code}")

test_endpoints()
