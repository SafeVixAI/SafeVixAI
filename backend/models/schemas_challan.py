# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Challan / fine calculation Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChallanQuery(BaseModel):
    violation_code: str = Field(description="Violation code (e.g., MVA_185)")
    vehicle_class: str | None = Field(None, description="Vehicle class (e.g., LMV, HMV)")
    state_code: str | None = Field(None, description="Two-letter state code (e.g., TN)")
    is_repeat_offense: bool = Field(False, description="Whether this is a repeat offense")


class ChallanResponse(BaseModel):
    violation_code: str = Field(description="Violation code")
    violation_name: str = Field(description="Human-readable violation name")
    description: str | None = Field(None, description="Detailed description")
    section: str | None = Field(None, description="Legal section reference")
    source: str | None = Field(None, description="Source document")
    state: str | None = Field(None, description="Two-letter state code")
    base_amount: int = Field(0, description="Base fine amount")
    state_amount: int = Field(0, description="State-specific fine amount (if different)")
    total_amount: int = Field(..., description="Total fine amount (base + state adjustments)")
    currency: str = Field("INR", description="Currency code")
    is_repeat_offense: bool = Field(False, description="Whether repeat offense penalty applies")


class FinePredictionRequest(BaseModel):
    violation_code: str = Field(description="Violation code")
    state_code: str | None = Field(None, description="Two-letter state code")
    vehicle_class: str | None = Field(None, description="Vehicle class")
    is_repeat_offense: bool = Field(False, description="Repeat offense flag")


class FinePredictionResponse(BaseModel):
    predicted_amount: int = Field(description="Predicted fine amount")
    confidence: float = Field(description="Prediction confidence 0-1")
    similar_cases: int = Field(0, description="Number of similar cases used")
    factors: list[str] = Field(default_factory=list, description="Factors influencing the prediction")


class DisputeDraftRequest(BaseModel):
    violation_code: str = Field(description="Violation code being disputed")
    challan_amount: int = Field(description="Challan amount received")
    state_code: str | None = Field(None, description="State code")
    reason: str = Field(description="Reason for dispute")


class DisputeDraftResponse(BaseModel):
    draft_id: str = Field(description="Dispute draft reference ID")
    draft_text: str = Field(description="Generated dispute draft text")
    suggested_sections: list[str] = Field(default_factory=list, description="Suggested legal sections")
