"""Challan calculation examples — online, offline, and SQL."""
import httpx

BASE = "http://localhost:8000"


def calculate_online(violation_code: str, state: str = "tamil_nadu") -> dict:
    """Calculate fine for a traffic violation via API."""
    resp = httpx.get(
        f"{BASE}/api/v1/challan/calculate",
        params={"violation_code": violation_code, "state": state},
    )
    resp.raise_for_status()
    return resp.json()


def calculate_with_vehicle_class(
    violation_code: str, state: str, vehicle_class: str
) -> dict:
    """Calculate fine with vehicle class override."""
    resp = httpx.get(
        f"{BASE}/api/v1/challan/calculate",
        params={
            "violation_code": violation_code,
            "state": state,
            "vehicle_class": vehicle_class,
        },
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # Basic fine
    result = calculate_online("MVA_185", "tamil_nadu")
    print(f"Drunk driving: ₹{result['amount']} — {result['description']}")

    # With vehicle class
    result = calculate_with_vehicle_class("MVA_194D", "karnataka", "motorcycle")
    print(f"No helmet in Karnataka: ₹{result['amount']}")
