import requests
import json


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

def ask_model_stream(prompt: str, model: str = "qwen2.5-coder:7b"):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        stream=True,
        timeout=120,
    )

    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "message" in data and "content" in data["message"]:
            yield data["message"]["content"]

        # Ollama sends a final chunk with "done": true
        if data.get("done", False):
            break