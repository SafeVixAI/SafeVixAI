# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.context_assembler import ContextAssembler
from agent.state import ConversationContext


class FakeRetriever:
    def __init__(self, *, return_results=True):
        self.return_results = return_results

    async def retrieve(self, query, *, top_k=None, scopes=None):
        if not self.return_results:
            return []
        return [
            SimpleNamespace(
                source="kb:general",
                title="SafeVixAI Knowledge Base",
                category="general",
                content=f"Reference for: {query}",
                score=0.98,
            )
        ]


class FakeSosTool:
    def __init__(self, include_w3w=False, return_empty=False):
        self._include_w3w = include_w3w
        self._return_empty = return_empty

    async def get_payload(self, *, lat, lon):
        if self._return_empty:
            return None
        payload = {
            "numbers": {"112": {"service": "Emergency"}, "108": {"service": "Ambulance"}},
            "services": [{"name": "City Hospital"}, {"name": "Police Station"}],
        }
        if self._include_w3w:
            payload["what3words"] = {"formatted": "///test.word.here"}
        return payload


class FakeWeatherTool:
    def __init__(self, return_empty=False):
        self._return_empty = return_empty

    async def lookup(self, *, lat, lon):
        if self._return_empty:
            return None
        return {"summary": "clear skies", "temperature": 29}

    async def aclose(self):
        pass


class FakeChallanTool:
    async def infer_and_calculate(self, message, client_ip=None):
        return {"section": "185", "base_fine": 10000, "repeat_fine": 15000, "amount_due": 10000}


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
        return {"title": "Bleeding Control", "steps": ["Apply direct pressure.", "Call emergency services."]}


class FakeRoadInfrastructureTool:
    def __init__(self, return_empty=False):
        self._return_empty = return_empty

    async def lookup(self, *, lat, lon):
        if self._return_empty:
            return None
        return {"exec_engineer": "Highways Department", "road_type": "Urban road", "road_type_code": "URB"}


class FakeRoadIssuesTool:
    def __init__(self, return_empty=False, issues=None):
        self._return_empty = return_empty
        self._issues = issues if issues is not None else [{"id": "issue-1"}]

    async def lookup(self, *, lat, lon):
        if self._return_empty:
            return None
        return {"count": len(self._issues), "issues": self._issues}


class FakeSubmitReportTool:
    def build_guidance(self, *, issue_type, lat, lon):
        return {"summary": f"Report guidance for {issue_type}."}

    async def aclose(self):
        pass


class FakeDrugInfoTool:
    def __init__(self, return_result=True):
        self._return_result = return_result

    async def lookup(self, drug):
        if not self._return_result:
            return None
        return {"indications": "Test drug indication for " + drug}


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


def make_context(**overrides) -> ConversationContext:
    ctx = ConversationContext(
        session_id=overrides.get("session_id", "test"),
        message=overrides.get("message", "test message"),
        intent=overrides.get("intent", "general"),
        lat=overrides.get("lat", 13.0827),
        lon=overrides.get("lon", 80.2707),
        client_ip=overrides.get("client_ip"),
        history=overrides.get("history", []),
    )
    return ctx








class TestAddWeatherContext:
    @pytest.mark.asyncio
    async def test_without_location_adds_requires_location(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
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
        ctx = make_context(lat=None, lon=None)
        await assembler._add_weather_context(ctx)
        assert len(ctx.tools) == 1
        assert ctx.tools[0].name == "road_weather"
        assert ctx.tools[0].payload.get("requires_location") is True

    @pytest.mark.asyncio
    async def test_with_location_adds_weather(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
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
        ctx = make_context(lat=13.0, lon=80.0)
        await assembler._add_weather_context(ctx)
        assert len(ctx.tools) == 1
        assert ctx.tools[0].name == "road_weather"
        assert "clear skies" in ctx.tools[0].summary
        assert ctx.tools[0].payload is not None

    @pytest.mark.asyncio
    async def test_with_location_but_empty_weather(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=FakeSosTool(),
            challan_tool=FakeChallanTool(),
            legal_search_tool=FakeLegalSearchTool(retriever),
            first_aid_tool=FakeFirstAidTool(),
            road_infra_tool=FakeRoadInfrastructureTool(),
            road_issues_tool=FakeRoadIssuesTool(),
            submit_report_tool=FakeSubmitReportTool(),
            weather_tool=FakeWeatherTool(return_empty=True),
            drug_info_tool=FakeDrugInfoTool(),
        )
        ctx = make_context(lat=13.0, lon=80.0)
        await assembler._add_weather_context(ctx)
        assert len(ctx.tools) == 0





class TestAddInfrastructureContext:
    @pytest.mark.asyncio
    async def test_without_location_adds_requires_location(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
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
        ctx = make_context(lat=None, lon=None)
        await assembler._add_infrastructure_context(ctx)
        assert len(ctx.tools) == 1
        assert ctx.tools[0].name == "road_infrastructure"
        assert ctx.tools[0].payload.get("requires_location") is True

    @pytest.mark.asyncio
    async def test_with_location_adds_infra(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
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
        ctx = make_context(lat=13.0, lon=80.0)
        await assembler._add_infrastructure_context(ctx)
        assert len(ctx.tools) == 1
        assert ctx.tools[0].name == "road_infrastructure"
        assert "Highways Department" in ctx.tools[0].summary

    @pytest.mark.asyncio
    async def test_with_location_empty_infra(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=FakeSosTool(),
            challan_tool=FakeChallanTool(),
            legal_search_tool=FakeLegalSearchTool(retriever),
            first_aid_tool=FakeFirstAidTool(),
            road_infra_tool=FakeRoadInfrastructureTool(return_empty=True),
            road_issues_tool=FakeRoadIssuesTool(),
            submit_report_tool=FakeSubmitReportTool(),
            weather_tool=FakeWeatherTool(),
            drug_info_tool=FakeDrugInfoTool(),
        )
        ctx = make_context(lat=13.0, lon=80.0)
        await assembler._add_infrastructure_context(ctx)
        assert len(ctx.tools) == 0


class TestAssembleIntentPaths:
    @pytest.mark.asyncio
    async def test_emergency_with_lat_lon_adds_sos_weather_and_w3w(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=FakeSosTool(include_w3w=True),
            challan_tool=FakeChallanTool(),
            legal_search_tool=FakeLegalSearchTool(retriever),
            first_aid_tool=FakeFirstAidTool(),
            road_infra_tool=FakeRoadInfrastructureTool(),
            road_issues_tool=FakeRoadIssuesTool(),
            submit_report_tool=FakeSubmitReportTool(),
            weather_tool=FakeWeatherTool(),
            drug_info_tool=FakeDrugInfoTool(),
        )
        context = await assembler.assemble(
            session_id="test",
            message="I need help",
            intent="emergency",
            lat=13.0,
            lon=80.0,
            history=[],
        )
        sos_tools = [t for t in context.tools if t.name == "sos"]
        weather_tools = [t for t in context.tools if t.name == "weather"]
        assert len(sos_tools) == 1
        assert len(weather_tools) == 1
        assert "What3Words" in sos_tools[0].summary

    @pytest.mark.asyncio
    async def test_emergency_without_lat_lon_does_rag_only(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="I need help",
            intent="emergency",
            lat=None,
            lon=None,
            history=[],
        )
        sos_tools = [t for t in context.tools if t.name == "sos"]
        assert len(sos_tools) == 0
        assert len(context.retrieved) >= 1

    @pytest.mark.asyncio
    async def test_road_issue_without_lat_lon(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="pothole on the road",
            intent="road_issue",
            lat=None,
            lon=None,
            history=[],
        )
        infra_tools = [t for t in context.tools if t.name == "road_infrastructure"]
        assert len(infra_tools) == 0
        assert len(context.retrieved) >= 1

    @pytest.mark.asyncio
    async def test_road_weather_intent(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="is it raining?",
            intent="road_weather",
            lat=None,
            lon=None,
            history=[],
        )
        weather_tools = [t for t in context.tools if t.name == "road_weather"]
        assert len(weather_tools) == 1
        assert weather_tools[0].payload.get("requires_location") is True

    @pytest.mark.asyncio
    async def test_safe_route_intent(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="navigate safely",
            intent="safe_route",
            lat=13.0,
            lon=80.0,
            history=[],
        )
        route_tools = [t for t in context.tools if t.name == "safe_route"]
        assert len(route_tools) == 1

    @pytest.mark.asyncio
    async def test_road_infrastructure_intent(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="who maintains this road",
            intent="road_infrastructure",
            lat=13.0,
            lon=80.0,
            history=[],
        )
        infra_tools = [t for t in context.tools if t.name == "road_infrastructure"]
        assert len(infra_tools) == 1
        assert "Highways Department" in infra_tools[0].summary

    @pytest.mark.asyncio
    async def test_road_infrastructure_without_location(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="who maintains this road",
            intent="road_infrastructure",
            lat=None,
            lon=None,
            history=[],
        )
        infra_tools = [t for t in context.tools if t.name == "road_infrastructure"]
        assert len(infra_tools) == 1
        assert infra_tools[0].payload.get("requires_location") is True

    @pytest.mark.asyncio
    async def test_first_aid_with_drug_info(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=FakeSosTool(),
            challan_tool=FakeChallanTool(),
            legal_search_tool=FakeLegalSearchTool(retriever),
            first_aid_tool=FakeFirstAidTool(),
            road_infra_tool=FakeRoadInfrastructureTool(),
            road_issues_tool=FakeRoadIssuesTool(),
            submit_report_tool=FakeSubmitReportTool(),
            weather_tool=FakeWeatherTool(),
            drug_info_tool=FakeDrugInfoTool(return_result=True),
        )
        context = await assembler.assemble(
            session_id="test",
            message="What about aspirin for pain?",
            intent="first_aid",
            lat=None,
            lon=None,
            history=[],
        )
        tool_names = [t.name for t in context.tools]
        assert "first_aid" in tool_names
        assert "drug_info" in tool_names

    @pytest.mark.asyncio
    async def test_first_aid_without_drug_info(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=FakeSosTool(),
            challan_tool=FakeChallanTool(),
            legal_search_tool=FakeLegalSearchTool(retriever),
            first_aid_tool=FakeFirstAidTool(),
            road_infra_tool=FakeRoadInfrastructureTool(),
            road_issues_tool=FakeRoadIssuesTool(),
            submit_report_tool=FakeSubmitReportTool(),
            weather_tool=FakeWeatherTool(),
            drug_info_tool=FakeDrugInfoTool(return_result=False),
        )
        context = await assembler.assemble(
            session_id="test",
            message="How to treat a burn?",
            intent="first_aid",
            lat=None,
            lon=None,
            history=[],
        )
        tool_names = [t.name for t in context.tools]
        assert "first_aid" in tool_names
        assert "drug_info" not in tool_names

    @pytest.mark.asyncio
    async def test_submit_report_context_offers_guidance(self, assembler):
        context = await assembler.assemble(
            session_id="test",
            message="I want to report a road hazard",
            intent="road_issue",
            lat=13.0,
            lon=80.0,
            history=[],
        )
        report_tools = [t for t in context.tools if t.name == "submit_report"]
        assert len(report_tools) == 0


class TestAddRetrieved:
    def test_add_retrieved_limits_to_5(self):
        retriever = FakeRetriever()
        assembler = ContextAssembler(
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
        many_results = [
            SimpleNamespace(source=f"kb:{i}", title=f"Doc {i}", category="general", content=f"Content {i}", score=0.9)
            for i in range(10)
        ]
        context = make_context()
        assembler._add_retrieved(context, many_results)
        assert len(context.retrieved) == 5
