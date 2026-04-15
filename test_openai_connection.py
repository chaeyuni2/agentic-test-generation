import os
from openai import OpenAI

print("OPENAI_API_KEY exists:", bool(os.getenv("OPENAI_API_KEY")))
print("OPENAI_MODEL:", os.getenv("OPENAI_MODEL"))
print("OPENAI_BASE_URL:", os.getenv("OPENAI_BASE_URL"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input="Reply with exactly: connected"
    )
    print("SUCCESS")
    print(response.output_text)
except Exception as e:
    print(type(e).__name__)
    print(e)