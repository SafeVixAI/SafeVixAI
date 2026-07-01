# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.context_assembler import ContextAssembler


class FakeRetriever:
    def __init__(self, *, return_results=True):
        self.return_results = return_results

    async def retrieve(self, query, *, top_k=None, scopes=None):
        if not self.return_results:
            return []
        source = "kb:emergency" if scopes else "kb:general"
        category = "emergency" if scopes else "general"
        return [
            SimpleNamespace(
                source=source,
                title="SafeVixAI Knowledge Base",
                category=category,
                content=f"Reference for: {query}",
                score=0.98,
            )
        ]


class FakeSosTool:
    async def get_payload(self, *, lat, lon):
        return {
            "numbers": {
                "112": {"service": "Emergency"},
                "108": {"service": "Ambulance"},
            },
            "services": [
                {"name": "City Hospital"},
                {"name": "Police Station"},
            ],
        }


class FakeWeatherTool:
    async def lookup(self, *, lat, lon):
        return {"summary": "clear skies", "temperature": 29}

    async def aclose(self):
        pass


class FakeChallanTool:
    async def infer_and_calculate(self, message, client_ip=None):
        return {
            "section": "185",
            "base_fine": 10000,
            "repeat_fine": 15000,
            "amount_due": 10000,
        }


class FakeLegalSearchTool:
    def __init__(self, retriever):
        self.retriever = retriever

    async def search(self, message):
        return [
            SimpleNamespace(
                source="kb:legal",
                title="Motor Vehicles Act",
                category="legal",
                content=f"Legal reference for: {message}",
                score=0.96,
            )
        ]


class FakeFirstAidTool:
    def lookup(self, message):
        return {
            "title": "Bleeding Control",
            "steps": ["Apply direct pressure.", "Call emergency services."],
        }


class FakeRoadInfrastructureTool:
    async def lookup(self, *, lat, lon):
        return {
            "exec_engineer": "Highways Department",
            "road_type": "Urban road",
            "road_type_code": "URB",
        }


class FakeRoadIssuesTool:
    async def lookup(self, *, lat, lon):
        return {"count": 1, "issues": [{"id": "issue-1"}]}


class FakeSubmitReportTool:
    def build_guidance(self, *, issue_type, lat, lon):
        return {"summary": f"Report guidance for {issue_type}."}

    async def aclose(self):
        pass


class FakeDrugInfoTool:
    async def lookup(self, drug):
        return {"indications": "Test drug indication"}


@pytest.fixture
def assembler():
    retriever = FakeRetriever()
    return ContextAssembler(
        retriever=retriever,
        sos_tool=FakeSosTool(),
        challan_tool=FakeChallanTool(),
        legal_search_tool=FakeLegalSearchTool(retriever),
        first_aid_tool=FakeFirstAidTool(),
        road_infra_tool=FakeRoadInfrastructureTool(),
        road_issues_tool=FakeRoadIssuesTool(),
        submit_report_tool=FakeSubmitReportTool(),
        weather_tool=FakeWeatherTool(),
        drug_info_tool=FakeDrugInfoTool(),
    )


@pytest.mark.asyncio
async def test_emergency_intent(assembler):
    context = await assembler.assemble(
        session_id="test-1",
        message="I need an ambulance near Anna Nagar",
        intent="emergency",
        lat=13.0878,
        lon=80.2087,
        history=[],
    )

    assert context.intent == "emergency"
    sos_tools = [t for t in context.tools if t.name == "sos"]
    assert len(sos_tools) >= 1
    assert any("City Hospital" in t.summary for t in sos_tools)
    weather_tools = [t for t in context.tools if t.name == "weather"]
    assert len(weather_tools) >= 1
    assert len(context.retrieved) >= 1


@pytest.mark.asyncio
async def test_first_aid_intent(assembler):
    context = await assembler.assemble(
        session_id="test-2",
        message="How to stop bleeding from a wound?",
        intent="first_aid",
        lat=None,
        lon=None,
        history=[],
    )

    assert context.intent == "first_aid"
    first_aid_tools = [t for t in context.tools if t.name == "first_aid"]
    assert len(first_aid_tools) >= 1
    assert "Bleeding Control" in first_aid_tools[0].summary


@pytest.mark.asyncio
async def test_challan_intent(assembler):
    context = await assembler.assemble(
        session_id="test-3",
        message="What is the fine for drunk driving?",
        intent="challan",
        lat=None,
        lon=None,
        history=[],
    )

    assert context.intent == "challan"
    challan_tools = [t for t in context.tools if t.name == "challan"]
    assert len(challan_tools) >= 1
    assert "185" in challan_tools[0].summary


@pytest.mark.asyncio
async def test_legal_intent(assembler):
    context = await assembler.assemble(
        session_id="test-4",
        message="What does Section 185 say?",
        intent="legal",
        lat=None,
        lon=None,
        history=[],
    )

    assert context.intent == "legal"
    assert len(context.retrieved) >= 1
    assert any("legal" in r.category.lower() for r in context.retrieved)


@pytest.mark.asyncio
async def test_road_issue_intent(assembler):
    context = await assembler.assemble(
        session_id="test-5",
        message="There is a big pothole on my road, report it",
        intent="road_issue",
        lat=13.0827,
        lon=80.2707,
        history=[],
    )

    assert context.intent == "road_issue"
    assert len(context.tools) >= 1


@pytest.mark.asyncio
async def test_road_weather_intent(assembler):
    context = await assembler.assemble(
        session_id="test-6",
        message="Is it safe to drive in this rain?",
        intent="road_weather",
        lat=13.0827,
        lon=80.2707,
        history=[],
    )

    assert context.intent == "road_weather"
    weather_tools = [t for t in context.tools if t.name == "road_weather"]
    assert len(weather_tools) >= 1


@pytest.mark.asyncio
async def test_safe_route_intent(assembler):
    context = await assembler.assemble(
        session_id="test-7",
        message="What is the safest route from Anna Nagar to T Nagar?",
        intent="safe_route",
        lat=13.0827,
        lon=80.2707,
        history=[],
    )

    assert context.intent == "safe_route"
    route_tools = [t for t in context.tools if t.name == "safe_route"]
    assert len(route_tools) >= 1


@pytest.mark.asyncio
async def test_road_infrastructure_intent(assembler):
    context = await assembler.assemble(
        session_id="test-8",
        message="Who maintains this road?",
        intent="road_infrastructure",
        lat=13.0827,
        lon=80.2707,
        history=[],
    )

    assert context.intent == "road_infrastructure"
    infra_tools = [t for t in context.tools if t.name == "road_infrastructure"]
    assert len(infra_tools) >= 1


@pytest.mark.asyncio
async def test_general_intent(assembler):
    context = await assembler.assemble(
        session_id="test-9",
        message="Tell me about road safety in India",
        intent="general",
        lat=None,
        lon=None,
        history=[],
    )

    assert context.intent == "general"
    assert len(context.retrieved) >= 1


@pytest.mark.asyncio
async def test_missing_location_graceful(assembler):
    context = await assembler.assemble(
        session_id="test-10",
        message="I need emergency help",
        intent="emergency",
        lat=None,
        lon=None,
        history=[],
    )

    assert context.intent == "emergency"
    sos_tools = [t for t in context.tools if t.name == "sos"]
    assert len(sos_tools) == 0
