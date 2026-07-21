# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import logging
import json
from dataclasses import dataclass
from typing import Any

from providers.base import ProviderRequest
from providers.router import ProviderRouter

logger = logging.getLogger(__name__)

@dataclass
class PlanStep:
    step: str
    tool_name: str | None = None
    completed: bool = False
    result: str | None = None

class PlanAndExecuteAgent:
    def __init__(self, provider_router: ProviderRouter, tools: dict[str, Any]):
        self.provider_router = provider_router
        self.tools = tools

    async def generate_plan(self, message: str) -> list[PlanStep]:
        # Minimal LLM call to get a plan
        system_prompt = (
            "You are a planning agent. Break down the user's request into smaller steps. "
            f"Available tools: {list(self.tools.keys())}. "
            "Output JSON with a list of steps: [{'step': '...', 'tool_name': '...'}]."
        )
        try:
            req = ProviderRequest(
                message=message,
                intent="general",
                history=[],
                tool_summaries=[system_prompt],
                document_snippets=[],
            )
            resp = await self.provider_router.generate(req)
            
            # Simple json parse (assume the model outputs valid json)
            text = resp.text
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end != 0:
                raw_steps = json.loads(text[start:end])
                return [PlanStep(step=s.get('step'), tool_name=s.get('tool_name')) for s in raw_steps]
        except Exception as e:
            logger.warning("Failed to generate plan: %s", e)
            
        return [PlanStep(step=message)]

    async def execute_step(self, step: PlanStep, context: dict) -> str:
        if step.tool_name and step.tool_name in self.tools:
            tool = self.tools[step.tool_name]
            try:
                if hasattr(tool, 'lookup'):
                    import inspect
                    sig = inspect.signature(tool.lookup)
                    if 'lat' in sig.parameters and 'lat' in context:
                        res = await tool.lookup(lat=context.get('lat'), lon=context.get('lon'))
                    else:
                        res = tool.lookup(step.step)
                        if inspect.isawaitable(res):  # pragma: no branch
                            res = await res
                    return str(res)
            except Exception as e:
                return f"Tool {step.tool_name} failed: {e}"
        
        # Fallback to LLM reasoning if no tool
        req = ProviderRequest(
            message=f"Solve this step: {step.step}\nContext: {json.dumps(context)}",
            intent="general",
            history=[],
            tool_summaries=[],
            document_snippets=[],
        )
        resp = await self.provider_router.generate(req)
        return resp.text

    async def run(self, message: str, context: dict) -> str:
        plan = await self.generate_plan(message)
        results = []
        for step in plan:
            result = await self.execute_step(step, context)
            step.result = result
            step.completed = True
            results.append(f"Step: {step.step}\nResult: {result}")
            
        # Final synthesis
        synthesis_req = ProviderRequest(
            message=message,
            intent="general",
            history=[],
            tool_summaries=["Synthesis context:\n" + "\n\n".join(results)],
            document_snippets=[],
        )
        synthesis = await self.provider_router.generate(synthesis_req)
        return synthesis.text
