"""Cookbook recipes — common SafeVixAI integration patterns."""
import httpx

BACKEND = "http://localhost:8000"
CHATBOT = "http://localhost:8010"


def recipe_emergency_alert(lat: float, lon: float) -> None:
    """Recipe 1: Emergency Alert System — find nearest hospital + generate share link."""
    hospital = httpx.get(
        f"{BACKEND}/api/v1/emergency/nearby",
        params={"lat": lat, "lon": lon, "type": "hospital", "limit": 1},
    ).json()

    whatsapp_link = (
        f"https://wa.me/?text=Emergency!%20"
        f"Location:%20https://maps.google.com/maps?q={lat},{lon}"
    )
    print(f"Nearest: {hospital}")
    print(f"Share: {whatsapp_link}")


def recipe_road_report_bot(lat: float, lon: float) -> str:
    """Recipe 2: Road Report Bot — submit road issue."""
    report = {
        "lat": lat,
        "lon": lon,
        "issue_type": "pothole",
        "severity": "high",
        "description": "Deep pothole on Anna Salai near Spencer Plaza",
        "photos": [],
    }

    resp = httpx.post(f"{BACKEND}/api/v1/roadwatch/report", json=report)
    resp.raise_for_status()
    uuid = resp.json()["uuid"]
    print(f"Report submitted: {uuid}")
    return uuid


def recipe_challan_checker() -> None:
    """Recipe 3: Bulk challan checker."""
    violations = [
        ("MVA_185", "tamil_nadu"),
        ("MVA_194D", "karnataka"),
        ("MVA_194B", "mumbai"),
    ]

    for code, state in violations:
        resp = httpx.get(
            f"{BACKEND}/api/v1/challan/calculate",
            params={"violation_code": code, "state": state},
        )
        data = resp.json()
        print(f"{code} in {state}: ₹{data['amount']}")


def recipe_multilingual_assistant() -> None:
    """Recipe 5: Multi-lingual assistant via Sarvam AI."""
    queries = [
        ("தமிழ்", "சென்னையில் அருகில் உள்ள மருத்துவமனை எது?"),
        ("हिन्दी", "तेज़ गति के लिए जुर्माना क्या है?"),
        ("తెలుగు", "దగ్గరలోని పోలీస్ స్టేషన్ ఎక్కడ?"),
    ]

    for lang, query in queries:
        resp = httpx.post(
            f"{CHATBOT}/api/v1/chat/",
            json={"message": query, "session_id": f"demo-{lang}"},
        )
        print(f"[{lang}] {resp.json()['response'][:100]}")


if __name__ == "__main__":
    recipe_emergency_alert(13.0827, 80.2707)
    recipe_road_report_bot(13.0827, 80.2707)
    recipe_challan_checker()
    recipe_multilingual_assistant()
