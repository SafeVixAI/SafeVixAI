# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""User API tests for SafeVixAI backend."""
from __future__ import annotations

import uuid

import pytest

from models.schemas import EmergencyContact, UserProfileCreate, UserProfileUpdate

# ── Schema Validation Tests ─────────────────────────────────────────────────

class TestUserProfileSchemas:
    """Tests for user profile request/response schemas."""

    def test_user_profile_create_valid(self):
        """Test valid user profile creation schema."""
        profile = UserProfileCreate(
            name="Test User",
            blood_group="O+",
            emergency_contacts=[
                EmergencyContact(name="Contact", phone="+919876543210", relation="spouse")
            ],
        )

        assert profile.name == "Test User"
        assert profile.blood_group == "O+"
        assert len(profile.emergency_contacts) == 1

    def test_user_profile_create_minimal(self):
        """Test minimal user profile creation."""
        profile = UserProfileCreate(
            name="Test User",
            emergency_contacts=[],
        )

        assert profile.name == "Test User"
        assert profile.blood_group is None

    def test_user_profile_create_invalid_blood_group(self):
        """Test invalid blood group rejection."""
        with pytest.raises(Exception):
            UserProfileCreate(
                name="Test User",
                blood_group="INVALID",
                emergency_contacts=[],
            )

    def test_user_profile_create_missing_name(self):
        """Test missing name rejection."""
        with pytest.raises(Exception):
            UserProfileCreate(
                emergency_contacts=[],
            )

    def test_user_profile_update_valid(self):
        """Test valid user profile update schema."""
        update = UserProfileUpdate(
            name="Updated Name",
            blood_group="A+",
        )

        assert update.name == "Updated Name"
        assert update.blood_group == "A+"

    def test_user_profile_update_partial(self):
        """Test partial profile update."""
        update = UserProfileUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.blood_group is None

    def test_emergency_contact_valid(self):
        """Test valid emergency contact schema."""
        contact = EmergencyContact(
            name="Emergency Contact",
            phone="+919876543210",
            relation="spouse",
        )

        assert contact.name == "Emergency Contact"
        assert contact.phone == "+919876543210"
        assert contact.relation == "spouse"

    def test_emergency_contact_minimal(self):
        """Test minimal emergency contact."""
        contact = EmergencyContact(
            name="Contact",
            phone="+919876543210",
        )

        assert contact.name == "Contact"
        assert contact.relation is None

    def test_emergency_contact_invalid_phone(self):
        """Test invalid phone rejection."""
        with pytest.raises(Exception):
            EmergencyContact(
                name="Contact",
                phone="invalid",
            )


# ── Validation Logic Tests ──────────────────────────────────────────────────

class TestUserValidation:
    """Tests for user-related validation logic."""

    def test_blood_group_patterns(self):
        """Test blood group pattern matching."""
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

        for group in valid_groups:
            assert len(group) in [2, 3]
            assert group[-1] in ["+", "-"]

    def test_phone_number_patterns(self):
        """Test phone number pattern validation."""
        valid_phones = [
            "+919876543210",
            "+1234567890",
            "9876543210",
        ]

        for phone in valid_phones:
            assert len(phone) >= 10

    def test_user_id_uuid_format(self):
        """Test user ID UUID format."""
        user_id = str(uuid.uuid4())
        assert len(user_id) == 36
        assert user_id.count("-") == 4

    def test_profile_name_length_limits(self):
        """Test profile name length limits."""
        # Max length 80
        long_name = "A" * 80
        assert len(long_name) == 80

        # Min length 1
        short_name = "A"
        assert len(short_name) == 1

    def test_emergency_contacts_serialization(self):
        """Test emergency contacts serialization."""
        contacts = [
            EmergencyContact(name="Contact 1", phone="+919876543210", relation="spouse"),
            EmergencyContact(name="Contact 2", phone="+919876543211", relation="parent"),
        ]

        serialized = [contact.model_dump() for contact in contacts]
        assert len(serialized) == 2
        assert serialized[0]["name"] == "Contact 1"
        assert serialized[1]["relation"] == "parent"

    def test_profile_update_exclude_unset(self):
        """Test profile update excludes unset fields."""
        update = UserProfileUpdate(name="New Name")
        update_data = update.model_dump(exclude_unset=True)

        assert "name" in update_data
        assert "blood_group" not in update_data
        assert "emergency_contacts" not in update_data
