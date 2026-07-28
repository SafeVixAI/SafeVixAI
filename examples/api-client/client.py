"""SafeVixAI Python API client example."""
import httpx
from typing import Any


class SafeVixAIClient:
    """Minimal API client for SafeVixAI services."""

    def __init__(self, backend_url: str = "http://localhost:8000", token: str | None = None):
        self.backend_url = backend_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def nearby_emergency(
        self, lat: float, lon: float, radius: int = 5000
    ) -> dict[str, Any]:
        """Get nearby hospitals, police stations, and fire stations."""
        resp = httpx.get(
            f"{self.backend_url}/api/v1/emergency/nearby",
            params={"lat": lat, "lon": lon, "radius": radius},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def calculate_challan(
        self, violation_code: str, state: str = "tamil_nadu"
    ) -> dict[str, Any]:
        """Calculate traffic fine for a violation."""
        resp = httpx.get(
            f"{self.backend_url}/api/v1/challan/calculate",
            params={"violation_code": violation_code, "state": state},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def report_road_issue(
        self, lat: float, lon: float, issue_type: str, description: str
    ) -> dict[str, Any]:
        """Submit a road damage report."""
        resp = httpx.post(
            f"{self.backend_url}/api/v1/roadwatch/report",
            json={
                "lat": lat,
                "lon": lon,
                "issue_type": issue_type,
                "description": description,
            },
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    client = SafeVixAIClient()
    emergency = client.nearby_emergency(13.0827, 80.2707)
    print(f"Hospitals: {len(emergency.get('hospitals', []))}")
