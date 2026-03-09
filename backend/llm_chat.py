# llm_chat.py
import requests

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "gemma3:1b"

def chat_complete(messages, timeout=90):
    r = requests.post(OLLAMA, json={"model": MODEL, "messages": messages, "stream": False}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]
