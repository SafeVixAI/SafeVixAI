"""Emergency locator and SOS integration examples."""
import httpx

BACKEND = "http://localhost:8000"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}


def trigger_sos(lat: float, lon: float) -> dict:
    """Trigger SOS with current location (requires auth)."""
    resp = httpx.post(
        f"{BACKEND}/api/v1/live-tracking/trigger-sos",
        json={"lat": lat, "lon": lon},
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()


def nearby_emergency(lat: float, lon: float, radius: int = 5000) -> dict:
    """Look up nearby emergency services."""
    resp = httpx.get(
        f"{BACKEND}/api/v1/emergency/nearby",
        params={"lat": lat, "lon": lon, "radius": radius},
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    data = nearby_emergency(13.0827, 80.2707)
    print("Hospitals:", [h["name"] for h in data.get("hospitals", [])])
    print("Police:", [p["name"] for p in data.get("police", [])])
    print("Fire:", [f["name"] for f in data.get("fire", [])])
