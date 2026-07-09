# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

class SubAgentManager:
    @staticmethod
    def get_system_prompt_for_intent(intent: str) -> str | None:
        try:
            from prompts import get_sub_agent_prompt
            yaml_prompt = get_sub_agent_prompt(intent)
            if yaml_prompt:
                return yaml_prompt
        except ImportError:
            pass
        prompts = {
            'legal': "You are the SafeVixAI Legal Advisor sub-agent. You provide precise, factual legal information based on the Motor Vehicles Act and other relevant statutes. Do not give binding legal counsel.",
            'first_aid': "You are the SafeVixAI Medical Response sub-agent. You provide calm, accurate, and step-by-step first aid guidance. Always recommend seeking professional medical help.",
            'road_infrastructure': "You are the SafeVixAI Technical Analyst sub-agent. You specialize in road infrastructure, engineering, and maintenance authority structures.",
            'safe_route': "You are the SafeVixAI Route Planning sub-agent. You calculate and recommend the safest path based on real-time hazards, weather, and traffic conditions.",
            'challan': "You are the SafeVixAI Traffic Enforcement sub-agent. You evaluate traffic violations and calculate penalties according to official schedules.",
        }
        return prompts.get(intent)
