# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.plan_and_execute import PlanAndExecuteAgent, PlanStep
from providers.router import ProviderRouter


class TestPlanStep:
    def test_plan_step_defaults(self):
        step = PlanStep(step="do something")
        assert step.step == "do something"
        assert step.tool_name is None
        assert step.completed is False
        assert step.result is None

    def test_plan_step_full(self):
        step = PlanStep(step="do it", tool_name="weather", completed=True, result="done")
        assert step.step == "do it"
        assert step.tool_name == "weather"
        assert step.completed is True
        assert step.result == "done"


class TestPlanAndExecuteAgent:
    @pytest.fixture
    def router(self):
        mock = AsyncMock(spec=ProviderRouter)
        mock.generate.return_value = MagicMock(text="[{\"step\": \"check weather\", \"tool_name\": \"weather\"}]")
        return mock

    @pytest.fixture
    def tools(self):
        return {"weather": MagicMock()}

    @pytest.fixture
    def agent(self, router, tools):
        return PlanAndExecuteAgent(provider_router=router, tools=tools)

    @pytest.mark.asyncio
    async def test_generate_plan_success(self, agent, router):
        plan = await agent.generate_plan("What's the weather?")
        assert len(plan) == 1
        assert plan[0].step == "check weather"
        assert plan[0].tool_name == "weather"
        router.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_plan_fallback_on_error(self, agent, router):
        router.generate.side_effect = RuntimeError("LLM failed")
        plan = await agent.generate_plan("What's the weather?")
        assert len(plan) == 1
        assert plan[0].step == "What's the weather?"
        assert plan[0].tool_name is None

    @pytest.mark.asyncio
    async def test_execute_step_with_tool_and_no_lat_sig(self, agent):
        """When tool.lookup has no 'lat' param, fallback to step string."""
        agent.tools["weather"].lookup = AsyncMock(return_value="Sunny, 32")
        step = PlanStep(step="check weather", tool_name="weather")
        result = await agent.execute_step(step, {"lat": 13.0, "lon": 80.0})
        agent.tools["weather"].lookup.assert_called_once_with("check weather")
        assert result == "Sunny, 32"

    @pytest.mark.asyncio
    async def test_execute_step_tool_failure(self, agent):
        agent.tools["weather"].lookup = AsyncMock(side_effect=ValueError("API error"))
        step = PlanStep(step="check weather", tool_name="weather")
        result = await agent.execute_step(step, {})
        assert "failed" in result

    @pytest.mark.asyncio
    async def test_execute_step_no_tool(self, agent, router):
        router.generate.return_value = MagicMock(text="LLM reasoning result")
        step = PlanStep(step="think about it", tool_name=None)
        result = await agent.execute_step(step, {})
        router.generate.assert_called_once()
        assert result == "LLM reasoning result"

    @pytest.mark.asyncio
    async def test_run_full_flow(self, agent, router):
        router.generate.return_value = MagicMock(text="[{\"step\": \"check weather\", \"tool_name\": \"weather\"}]")
        agent.tools["weather"].lookup = AsyncMock(return_value="Sunny, 32")
        result = await agent.run("What's the weather?", {})
        assert "Sunny, 32" in result or "check weather" in result
        assert router.generate.call_count >= 2

    @pytest.mark.asyncio
    async def test_run_generate_plan_fallback_then_synthesis(self, router):
        router.generate.side_effect = [
            MagicMock(text="[{\"step\": \"hello\", \"tool_name\": null}]"),
            MagicMock(text="llm reasoning"),
            MagicMock(text="synthesis result"),
        ]
        agent = PlanAndExecuteAgent(provider_router=router, tools={})
        result = await agent.run("hello", {})
        assert result is not None
