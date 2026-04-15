import os
import requests

print("OPENAI_API_KEY exists:", bool(os.getenv("OPENAI_API_KEY")))

try:
    r = requests.get("https://api.openai.com/v1/models", timeout=15)
    print("NO AUTH STATUS:", r.status_code)
    print(r.text[:300])
except Exception as e:
    print("NO AUTH ERROR:", type(e).__name__, e)

try:
    r = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
        timeout=15,
    )
    print("AUTH STATUS:", r.status_code)
    print(r.text[:300])
except Exception as e:
    print("AUTH ERROR:", type(e).__name__, e)