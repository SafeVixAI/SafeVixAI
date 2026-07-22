# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""User / profile Pydantic schemas."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

BloodGroup = Literal['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


class EmergencyContact(BaseModel):
    name: str | None = Field(None, description="Contact person name")
    phone: str | None = Field(None, description="Contact phone number")
    relationship: str | None = Field(None, description="Relationship to user")


class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    display_id: str | None = Field(None, description="Public display ID")
    blood_group: BloodGroup | None = Field(None, description="Blood group (A+, O-, etc.)")
    vehicle_number: str | None = Field(None, max_length=20, description="Vehicle registration number")
    emergency_contact: str | None = Field(None, description="Emergency contact number")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    address: str | None = Field(None, description="Address")
    date_of_birth: date | None = Field(None, description="Date of birth (ISO 8601)")


class UserProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, description="Updated name")
    blood_group: BloodGroup | None = Field(None, description="Updated blood group")
    vehicle_number: str | None = Field(None, max_length=20, description="Updated vehicle number")
    emergency_contact: str | None = Field(None, description="Updated emergency contact")
    email: str | None = Field(None, description="Updated email")
    phone: str | None = Field(None, description="Updated phone")
    address: str | None = Field(None, description="Updated address")
    date_of_birth: date | None = Field(None, description="Updated date of birth")


class UserProfileResponse(UserProfileCreate):
    pass


class UserDataExport(BaseModel):
    profile: dict = Field(description="User profile data")
    incidents: list[dict] = Field(default_factory=list, description="Reported incidents")
    tracking_sessions: list[dict] = Field(default_factory=list, description="Tracking sessions")


class UserDeleteResponse(BaseModel):
    deleted: bool = Field(description="Whether the account was deleted")
    message: str = Field(description="Deletion confirmation message")
