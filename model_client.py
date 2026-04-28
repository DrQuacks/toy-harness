import requests


def ask_model(prompt: str, model: str = "qwen2.5-coder:7b") -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["message"]["content"]