from dotenv import load_dotenv
import os
import requests

load_dotenv()

token = os.getenv("LOGFIRE_TOKEN")
print(f"Token: {token[:20]}...")

# Test 1: Endpoint projects (devrait marcher avec project:read)
print("\n=== TEST 1: GET /v1/projects ===")
response = requests.get(
    "https://logfire-api.pydantic.dev/v1/projects",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 2: Endpoint OTLP (celui utilisé pour envoyer traces)
print("\n=== TEST 2: POST /v1/traces (OTLP endpoint) ===")
response = requests.post(
    "https://logfire-api.pydantic.dev/v1/traces",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"test": "data"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
