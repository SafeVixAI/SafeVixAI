from __future__ import annotations

from agent.sub_agents import SubAgentManager


class TestSubAgentManager:
    def test_get_system_prompt_for_intent_legal(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('legal')
        assert prompt is not None
        assert 'Legal Advisor' in prompt
        assert 'Motor Vehicles Act' in prompt

    def test_get_system_prompt_for_intent_first_aid(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('first_aid')
        assert prompt is not None
        assert 'Medical Response' in prompt

    def test_get_system_prompt_for_intent_road_infrastructure(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('road_infrastructure')
        assert prompt is not None
        assert 'Technical Analyst' in prompt

    def test_get_system_prompt_for_intent_safe_route(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('safe_route')
        assert prompt is not None
        assert 'Route Planning' in prompt

    def test_get_system_prompt_for_intent_challan(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('challan')
        assert prompt is not None
        assert 'Traffic Enforcement' in prompt

    def test_get_system_prompt_for_unknown_intent(self):
        prompt = SubAgentManager.get_system_prompt_for_intent('unknown_intent')
        assert prompt is None

    def test_get_system_prompt_for_none_intent(self):
        prompt = SubAgentManager.get_system_prompt_for_intent(None)
        assert prompt is None
