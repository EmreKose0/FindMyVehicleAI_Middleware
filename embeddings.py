import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def embed_text(text: str):
    payload = {"model": EMBED_MODEL, "prompt": text}
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["embedding"]


