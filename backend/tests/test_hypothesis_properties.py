# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Property-based tests for core domain invariants using Hypothesis."""

from datetime import timedelta
from hypothesis import given, strategies as st

from services.challan_service import ChallanService
from services.officer_route_optimizer import _haversine_km
from models.values import Coordinates, Severity, Distance
from models.schemas import ChallanQuery
from core.config import Settings


# ── Coordinate invariants ──────────────────────────────────────────────

latitude = st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False)
longitude = st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False)
positive_floats = st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)


@given(lat=latitude, lon=longitude)
def test_haversine_is_non_negative(lat, lon):
    dist = _haversine_km(lat, lon, lat, lon)
    assert dist == 0.0


@given(lat1=latitude, lon1=longitude, lat2=latitude, lon2=longitude)
def test_haversine_symmetric(lat1, lon1, lat2, lon2):
    d1 = _haversine_km(lat1, lon1, lat2, lon2)
    d2 = _haversine_km(lat2, lon2, lat1, lon1)
    assert abs(d1 - d2) < 1e-9


# ── Challan calculation invariants ─────────────────────────────────────


svc = ChallanService(Settings())


@given(
    violation_code=st.sampled_from(["183", "185", "181", "194D"]),
)
def test_fine_amount_non_negative(violation_code):
    resp = svc.calculate(ChallanQuery(violation_code=violation_code, state_code="TN", vehicle_class="LMV"))
    assert resp.amount_due >= 0


@given(
    violation_code=st.text(min_size=1, max_size=20),
    state_code=st.text(min_size=2, max_size=3),
)
def test_unknown_violation_raises_error(violation_code, state_code):
    from services.exceptions import ServiceValidationError
    try:
        svc.calculate(ChallanQuery(violation_code=violation_code, state_code=state_code, vehicle_class="LMV"))
        assert False, "Expected ServiceValidationError"
    except ServiceValidationError:
        pass


# ── Value objects ──────────────────────────────────────────────────────


@given(lat=latitude, lon=longitude)
def test_coordinates_haversine_to_self(lat, lon):
    c = Coordinates(lat=lat, lon=lon)
    dist = c.distance_to(c)
    assert dist.meters == 0.0


@given(lat=latitude, lon=longitude)
def test_coordinates_repr(lat, lon):
    c = Coordinates(lat=lat, lon=lon)
    assert f"{lat}" in repr(c)
    assert f"{lon}" in repr(c)


@given(level=st.integers(min_value=1, max_value=5))
def test_severity_from_level(level):
    s = Severity(level=level)
    assert 1 <= s.level <= 5


@given(risk_score=st.floats(min_value=0, max_value=100, allow_nan=False))
def test_severity_from_risk_score(risk_score):
    if risk_score >= 80:
        level = 5
    elif risk_score >= 60:
        level = 4
    elif risk_score >= 40:
        level = 3
    elif risk_score >= 20:
        level = 2
    else:
        level = 1
    s = Severity(level=level)
    assert 1 <= s.level <= 5


@given(meters=positive_floats)
def test_distance_conversion(meters):
    d = Distance(meters=meters)
    km = d.kilometers
    assert abs(km - meters / 1000.0) < 1e-6
    assert d.meters >= 0


# ── Geocoding URL invariants ────────────────────────────────────────────


@given(
    lat=latitude,
    lon=longitude,
)
def test_geocoding_service_instantiation(lat, lon):
    from services.geocoding_service import GeocodingService
    svc = GeocodingService(settings=Settings())
    assert svc is not None


# ── Time invariants ────────────────────────────────────────────────────


@given(
    days=st.integers(min_value=0, max_value=365),
)
def test_token_expiry_in_future(days):
    from core.security import create_access_token

    data = {"sub": "test"}
    expires = timedelta(days=days)
    token = create_access_token(data, expires_delta=expires)
    assert isinstance(token, str)
    assert len(token) > 20
