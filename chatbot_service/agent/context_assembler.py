# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
import re

from agent.state import ConversationContext, RetrievedContext, ToolContext
from memory.tiered_memory import TieredMemory
from rag.retriever import Retriever
from tools.challan_tool import ChallanTool
from tools.drug_info import DrugInfoTool
from tools.first_aid_tool import FirstAidTool
from tools.legal_search_tool import LegalSearchTool
from tools.road_infra_tool import RoadInfrastructureTool
from tools.road_issues_tool import RoadIssuesTool
from tools.sos_tool import SosTool
from tools.submit_report_tool import SubmitReportTool
from tools.weather_tool import WeatherTool

logger = logging.getLogger(__name__)


class ContextAssembler:
    def __init__(
        self,
        *,
        retriever: Retriever,
        sos_tool: SosTool,
        challan_tool: ChallanTool,
        legal_search_tool: LegalSearchTool,
        first_aid_tool: FirstAidTool,
        road_infra_tool: RoadInfrastructureTool,
        road_issues_tool: RoadIssuesTool,
        submit_report_tool: SubmitReportTool,
        weather_tool: WeatherTool,
        drug_info_tool: DrugInfoTool,
        episodic_memory_agent = None,
        tiered_memory: TieredMemory | None = None,
    ) -> None:
        self.retriever = retriever
        self.sos_tool = sos_tool
        self.challan_tool = challan_tool
        self.legal_search_tool = legal_search_tool
        self.first_aid_tool = first_aid_tool
        self.road_infra_tool = road_infra_tool
        self.road_issues_tool = road_issues_tool
        self.submit_report_tool = submit_report_tool
        self.weather_tool = weather_tool
        self.drug_info_tool = drug_info_tool
        self.episodic_memory_agent = episodic_memory_agent
        self.tiered_memory = tiered_memory

    async def assemble(
        self,
        *,
        session_id: str,
        message: str,
        intent: str,
        lat: float | None,
        lon: float | None,
        client_ip: str | None = None,
        history: list[dict],
        user_id: str | None = None,
    ) -> ConversationContext:
        context = ConversationContext(
            session_id=session_id,
            message=message,
            intent=intent,
            lat=lat,
            lon=lon,
            client_ip=client_ip,
            history=history,
        )

        # Tiered memory (user prefs + STM + LTM)
        if user_id and user_id not in ('anonymous', 'authenticated', ''):
            try:
                if self.tiered_memory:
                    tm_result = await self.tiered_memory.get_relevant(user_id, session_id, message)
                    if not tm_result.is_empty():
                        summary = tm_result.to_summary()
                        context.tools.append(
                            ToolContext(
                                name='tiered_memory',
                                summary=summary[:500],
                                payload={
                                    'preferences': tm_result.user_preferences,
                                    'stm': tm_result.stm_facts,
                                    'ltm': tm_result.ltm_memories,
                                },
                                sources=['memory:tiered'],
                            )
                        )
                elif self.episodic_memory_agent:
                    memories = self.episodic_memory_agent.retrieve_memory(user_id, message)
                    if memories:  # pragma: no branch
                        context.tools.append(
                            ToolContext(
                                name='episodic_memory',
                                summary='User context (remembered facts): ' + ' | '.join(memories),
                                payload={'memories': memories},
                                sources=['memory:episodic'],
                            )
                        )
            except (ValueError, KeyError, RuntimeError) as e:
                logger.warning("Tiered/episodic memory retrieval failed: %s", e)

        dispatch = {
            'emergency': self._assemble_emergency,
            'first_aid': self._assemble_first_aid,
            'challan': self._assemble_challan,
            'legal': self._assemble_legal,
            'road_issue': self._assemble_road_issue,
            'road_weather': self._assemble_road_weather,
            'safe_route': self._assemble_safe_route,
            'road_infrastructure': self._assemble_road_infrastructure,
        }
        handler = dispatch.get(intent, self._assemble_general)
        await handler(context, message)

        return context

    async def _assemble_emergency(self, context: ConversationContext, message: str) -> None:
        if context.lat is not None and context.lon is not None:
            sos_task = self.sos_tool.get_payload(lat=context.lat, lon=context.lon)
            weather_task = self.weather_tool.lookup(lat=context.lat, lon=context.lon)
            sos_payload, weather = await asyncio.gather(sos_task, weather_task, return_exceptions=True)

            if not isinstance(sos_payload, Exception) and sos_payload:
                numbers = sos_payload.get('numbers') or {}
                services = sos_payload.get('services') or []
                nearest_names = ', '.join(item.get('name', 'Unknown') for item in services[:3]) or 'No nearby services listed'
                number_text = ', '.join(f'{key}:{value.get("service")}' for key, value in numbers.items())

                w3w_text = ""
                if 'what3words' in sos_payload:
                    w3w_text = f" What3Words: {sos_payload['what3words'].get('formatted')}."

                context.tools.append(
                    ToolContext(
                        name='sos',
                        summary=f'Nearby emergency services: {nearest_names}. Emergency numbers: {number_text}.{w3w_text}',
                        payload=sos_payload,
                        sources=['tool:sos', 'backend:/api/v1/emergency/sos'],
                    )
                )
            if not isinstance(weather, Exception) and weather:  # pragma: no branch
                context.tools.append(
                    ToolContext(
                        name='weather',
                        summary=f'Local weather: {weather.get("summary")} at {weather.get("temperature")} degrees.',
                        payload=weather,
                        sources=['tool:weather'],
                    )
                )
        await self._add_rag_context(context, message, scopes={'medical', 'emergency', 'hospitals'})

    async def _assemble_first_aid(self, context: ConversationContext, message: str) -> None:
        await self._add_first_aid_context(context)
        await self._add_rag_context(context, message, scopes={'medical'})

    async def _assemble_challan(self, context: ConversationContext, message: str) -> None:
        await self._add_challan_context(context)
        self._add_retrieved(context, await self.legal_search_tool.search(message))

    async def _assemble_legal(self, context: ConversationContext, message: str) -> None:
        self._add_retrieved(context, await self.legal_search_tool.search(message))

    async def _assemble_road_issue(self, context: ConversationContext, message: str) -> None:
        if context.lat is not None and context.lon is not None:
            infra_task = self.road_infra_tool.lookup(lat=context.lat, lon=context.lon)
            issues_task = self.road_issues_tool.lookup(lat=context.lat, lon=context.lon)
            infrastructure, issues = await asyncio.gather(infra_task, issues_task, return_exceptions=True)

            if not isinstance(infrastructure, Exception) and infrastructure:
                context.tools.append(
                    ToolContext(
                        name='road_infrastructure',
                        summary=(
                            f'Road authority: {infrastructure.get("exec_engineer") or infrastructure.get("contractor_name") or infrastructure.get("road_type")}. '
                            f'Road type: {infrastructure.get("road_type")} ({infrastructure.get("road_type_code")}).'
                        ),
                        payload=infrastructure,
                        sources=['tool:road_infrastructure', 'backend:/api/v1/roads/infrastructure'],
                    )
                )
            if not isinstance(issues, Exception) and issues and (issues.get('issues') or []):
                count = issues.get('count') or len(issues.get('issues') or [])
                context.tools.append(
                    ToolContext(
                        name='road_issues',
                        summary=f'{count} nearby road issues are already reported in the selected radius.',
                        payload=issues,
                        sources=['tool:road_issues', 'backend:/api/v1/roads/issues'],
                    )
                )
        await self._add_rag_context(context, message, scopes={'roads', 'accidents'})

    async def _assemble_road_weather(self, context: ConversationContext, message: str) -> None:
        await self._add_weather_context(context)
        await self._add_rag_context(context, message, scopes={'roads', 'accidents'})

    async def _assemble_safe_route(self, context: ConversationContext, message: str) -> None:
        context.tools.append(
            ToolContext(
                name='safe_route',
                summary='For safest routing, collect origin, destination, current GPS, and avoid roads with severe reports, '
                        'poor visibility, flooding, or active incidents.',
                payload={'requires_origin_destination': True},
                sources=['tool:safe_route'],
            )
        )
        if context.lat is not None and context.lon is not None:  # pragma: no branch
            issues_task = self.road_issues_tool.lookup(lat=context.lat, lon=context.lon)
            weather_task = self.weather_tool.lookup(lat=context.lat, lon=context.lon)
            issues, weather = await asyncio.gather(issues_task, weather_task, return_exceptions=True)

            if not isinstance(issues, Exception) and issues and (issues.get('issues') or []):  # pragma: no branch
                count = issues.get('count') or len(issues.get('issues') or [])
                context.tools.append(
                    ToolContext(
                        name='route_risk',
                        summary=f'{count} reported road issues may affect route safety near the current location.',
                        payload=issues,
                        sources=['tool:road_issues', 'backend:/api/v1/roads/issues'],
                    )
                )
            if not isinstance(weather, Exception) and weather:  # pragma: no branch
                context.tools.append(
                    ToolContext(
                        name='route_weather',
                        summary=f'Weather risk near current location: {weather.get("summary")}.',
                        payload=weather,
                        sources=['tool:weather'],
                    )
                )
        await self._add_rag_context(context, message, scopes={'roads', 'accidents'})

    async def _assemble_road_infrastructure(self, context: ConversationContext, message: str) -> None:
        await self._add_infrastructure_context(context)
        await self._add_rag_context(context, message, scopes={'roads'})

    async def _assemble_general(self, context: ConversationContext, message: str) -> None:
        await self._add_rag_context(context, message)

    async def _add_first_aid_context(self, context: ConversationContext) -> None:
        guide = self.first_aid_tool.lookup(context.message)
        if guide:  # pragma: no branch
            steps = guide.get('steps') or []
            context.tools.append(
                ToolContext(
                    name='first_aid',
                    summary=f'{guide.get("title")}: ' + ' '.join(f'{index + 1}. {step}' for index, step in enumerate(steps[:4])),
                    payload=guide,
                    sources=['tool:first_aid'],
                )
            )

        # Extract potential drug name from message for OpenFDA
        words = context.message.lower().replace('?', '').replace(',', '').split()
        potential_drugs = [w for w in words if len(w) > 4 and w not in {'please', 'about', 'effects', 'dosage', 'should', 'take'}]
        for drug in potential_drugs[:2]:  # Try up to 2 words
            drug_info = await self.drug_info_tool.lookup(drug)
            if drug_info:
                context.tools.append(
                    ToolContext(
                        name='drug_info',
                        summary=f'FDA Info for {drug}: Indications: {drug_info.get("indications", "N/A")[:100]}...',
                        payload=drug_info,
                        sources=['tool:drug_info', 'openfda'],
                    )
                )
                break

    async def _add_challan_context(self, context: ConversationContext) -> None:
        challan = await self.challan_tool.infer_and_calculate(context.message, client_ip=context.client_ip)
        if challan:  # pragma: no branch
            context.tools.append(
                ToolContext(
                    name='challan',
                    summary=(
                        f'Applicable section: {challan.get("section")}. '
                        f'Base fine: INR {challan.get("base_fine")}. '
                        f'Repeat fine: {challan.get("repeat_fine")}. '
                        f'Amount due in this scenario: INR {challan.get("amount_due")}.'
                    ),
                    payload=challan,
                    sources=['tool:challan', 'backend:/api/v1/challan/calculate'],
                )
            )

    async def _add_weather_context(self, context: ConversationContext) -> None:
        if context.lat is None or context.lon is None:
            context.tools.append(
                ToolContext(
                    name='road_weather',
                    summary='Location is required for live road-weather lookup. Ask the user for GPS/location permission.',
                    payload={'requires_location': True},
                    sources=['tool:weather'],
                )
            )
            return

        weather = await self.weather_tool.lookup(lat=context.lat, lon=context.lon)
        if weather:
            context.tools.append(
                ToolContext(
                    name='road_weather',
                    summary=f'Local road-weather: {weather.get("summary")} at {weather.get("temperature")} degrees.',
                    payload=weather,
                    sources=['tool:weather'],
                )
            )

    async def _add_infrastructure_context(self, context: ConversationContext) -> None:
        if context.lat is None or context.lon is None:
            context.tools.append(
                ToolContext(
                    name='road_infrastructure',
                    summary='Location is required to identify the road owner or maintenance authority.',
                    payload={'requires_location': True},
                    sources=['tool:road_infrastructure'],
                )
            )
            return

        infrastructure = await self.road_infra_tool.lookup(lat=context.lat, lon=context.lon)
        if infrastructure:
            context.tools.append(
                ToolContext(
                    name='road_infrastructure',
                    summary=(
                        f'Road authority: {infrastructure.get("exec_engineer") or infrastructure.get("contractor_name") or infrastructure.get("road_type")}. '
                        f'Road type: {infrastructure.get("road_type")} ({infrastructure.get("road_type_code")}).'
                    ),
                    payload=infrastructure,
                    sources=['tool:road_infrastructure', 'backend:/api/v1/roads/infrastructure'],
                )
            )

    async def _add_rag_context(self, context: ConversationContext, message: str, scopes: set[str] | None = None) -> None:
        results = await self.retriever.retrieve(message, scopes=scopes)
        if not results:
            words = re.findall(r'\b\w+\b', message.lower())
            stopwords = {'is', 'the', 'a', 'an', 'what', 'where', 'how', 'why', 'who', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'my', 'i', 'need', 'help', 'with', 'can', 'you', 'tell', 'me', 'about', 'some', 'any'}
            keywords = [w for w in words if w not in stopwords]
            rewritten_query = ' '.join(keywords)
            if rewritten_query and rewritten_query != message.lower():
                logger.info("RAG Fallback: Rewriting query '%s' -> '%s'", message, rewritten_query)
                results = await self.retriever.retrieve(rewritten_query, scopes=scopes)
        self._add_retrieved(context, results)

    @staticmethod
    def _add_retrieved(context: ConversationContext, results) -> None:
        for item in results[:5]:
            context.retrieved.append(
                RetrievedContext(
                    source=item.source,
                    title=item.title,
                    snippet=item.content[:320],
                    score=item.score,
                    category=item.category,
                )
            )
