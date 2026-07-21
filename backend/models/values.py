# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Domain value objects — Coordinates, Severity, Distance."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    """A validated (lat, lon) coordinate pair."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"lat must be in [-90, 90], got {self.lat}")
        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError(f"lon must be in [-180, 180], got {self.lon}")

    def distance_to(self, other: Coordinates) -> Distance:
        """Haversine distance to another coordinate pair."""
        R = 6371_000  # Earth radius in meters
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(self.lat))
            * math.cos(math.radians(other.lat))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return Distance(meters=R * c)

    def as_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Severity:
    """A validated severity level (1-5)."""

    level: int

    def __post_init__(self) -> None:
        if not (1 <= self.level <= 5):
            raise ValueError(f"Severity must be 1-5, got {self.level}")

    @property
    def label(self) -> str:
        mapping = {1: "low", 2: "moderate", 3: "high", 4: "critical", 5: "emergency"}
        return mapping.get(self.level, "unknown")

    @property
    def is_critical(self) -> bool:
        return self.level >= 4

    @classmethod
    def from_int(cls, value: int) -> Severity:
        return cls(level=value)


@dataclass(frozen=True)
class Distance:
    """A validated distance in meters."""

    meters: float

    def __post_init__(self) -> None:
        if self.meters < 0:
            raise ValueError(f"Distance must be non-negative, got {self.meters}")

    @property
    def kilometers(self) -> float:
        return self.meters / 1000.0

    def __lt__(self, other: Distance) -> bool:
        return self.meters < other.meters

    def __le__(self, other: Distance) -> bool:
        return self.meters <= other.meters

    def __gt__(self, other: Distance) -> bool:
        return self.meters > other.meters

    def __ge__(self, other: Distance) -> bool:
        return self.meters >= other.meters

    def __add__(self, other: Distance) -> Distance:
        return Distance(meters=self.meters + other.meters)

    def __sub__(self, other: Distance) -> Distance:
        return Distance(meters=max(0.0, self.meters - other.meters))
