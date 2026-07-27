# Chatbot Integration Examples

> **Chat completion, streaming, and tool usage patterns.**

---

## Simple Chat

```python
import httpx

CHATBOT = "http://localhost:8010"

resp = httpx.post(
    f"{CHATBOT}/api/v1/chat/",
    json={
        "message": "What is the fine for speeding in Tamil Nadu?",
        "session_id": "user-session-123",
    },
)
print(resp.json()["response"])
```

## Streaming Chat

```python
import httpx

CHATBOT = "http://localhost:8010"

with httpx.stream(
    "POST",
    f"{CHATBOT}/api/v1/chat/stream",
    json={
        "message": "Tell me about first aid for burns",
        "session_id": "user-session-456",
    },
) as resp:
    for chunk in resp.iter_text():
        print(chunk, end="", flush=True)
```

## With Provider Override

```python
import httpx

resp = httpx.post(
    "http://localhost:8010/api/v1/chat/",
    json={
        "message": "Explain section 304A IPC",
        "session_id": "legal-user-789",
        "provider_hint": "gemini",
        "provider_model": "gemini-2.0-flash",
    },
)
print(resp.json()["response"])
```

## Using Agent Tools

```python
import httpx

# The chatbot automatically routes to appropriate tools based on intent
queries = [
    "What hospitals are near Chennai Central?",  # → SOS/Emergency tool
    "What's the fine for no helmet?",             # → Challan tool
    "How do I treat a deep cut?",                 # → FirstAid tool
    "Report a pothole on Mount Road",             # → SubmitReport tool
]

for q in queries:
    resp = httpx.post(
        "http://localhost:8010/api/v1/chat/",
        json={"message": q, "session_id": "demo"},
    )
    print(f"Q: {q}")
    print(f"A: {resp.json()['response'][:100]}...\n")
```
