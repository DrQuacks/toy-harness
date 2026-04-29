import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen2.5-coder:7b",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": "Write Python code that prints Hello, world! Return only code.",
            }
        ],
    },
    timeout=120,
)

response.raise_for_status()

print(response.json()["message"]["content"])