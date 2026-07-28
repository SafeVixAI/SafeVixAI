"""Chatbot integration examples — simple, streaming, provider override, tools."""
import httpx

CHATBOT = "http://localhost:8010"


def simple_chat(message: str, session_id: str = "demo") -> str:
    """Send a simple chat message and get a response."""
    resp = httpx.post(
        f"{CHATBOT}/api/v1/chat/",
        json={"message": message, "session_id": session_id},
    )
    resp.raise_for_status()
    return resp.json()["response"]


def streaming_chat(message: str, session_id: str = "demo") -> None:
    """Stream a chat response token by token."""
    with httpx.stream(
        "POST",
        f"{CHATBOT}/api/v1/chat/stream",
        json={"message": message, "session_id": session_id},
    ) as resp:
        for chunk in resp.iter_text():
            print(chunk, end="", flush=True)
    print()


def chat_with_provider(
    message: str,
    session_id: str,
    provider_hint: str,
    provider_model: str | None = None,
) -> str:
    """Chat with a specific LLM provider override."""
    body = {
        "message": message,
        "session_id": session_id,
        "provider_hint": provider_hint,
    }
    if provider_model:
        body["provider_model"] = provider_model

    resp = httpx.post(f"{CHATBOT}/api/v1/chat/", json=body)
    resp.raise_for_status()
    return resp.json()["response"]


if __name__ == "__main__":
    # Simple chat
    reply = simple_chat("What is the fine for speeding in Tamil Nadu?")
    print(f"Reply: {reply[:100]}...")

    # Provider override
    reply = chat_with_provider(
        "Explain section 304A IPC",
        "legal-user",
        provider_hint="gemini",
        provider_model="gemini-2.0-flash",
    )
    print(f"Legal: {reply[:100]}...")
