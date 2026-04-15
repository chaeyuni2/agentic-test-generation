import urllib.request

try:
    with urllib.request.urlopen("https://api.openai.com", timeout=10) as r:
        print("HTTPS OK", r.status)
except Exception as e:
    print(type(e).__name__)
    print(e)