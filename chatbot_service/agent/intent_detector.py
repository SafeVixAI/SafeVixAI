# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import re
from typing import Any

CHALLAN_CODE_PATTERN = re.compile(r'\b(?:179|181|183|185|194B|194D)\b', re.IGNORECASE)
INTENT_CLASSES = (
    'emergency',
    'first_aid',
    'challan',
    'legal',
    'road_issue',
    'road_weather',
    'safe_route',
    'road_infrastructure',
    'general',
)

_FOLLOW_UP_INDICATORS = (
    'what about', 'how about', 'and', 'also', 'what else', 'tell me more',
    'elaborate', 'explain more', 'give me more', 'more details',
    'what does that mean', 'can you explain', 'for example',
    'like what', 'such as', 'specifically', 'regarding',
)

_AMBIGUOUS_SHORT_MESSAGE_THRESHOLD = 5


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


from rag.embeddings import build_embedding_function

class IntentDetector:
    def __init__(self, embedding_model: str | None = None):
        resolved = embedding_model or 'sentence-transformers/all-MiniLM-L6-v2'
        self.embedding_function = build_embedding_function(resolved)
        self._embedding_model = resolved
        
        # Define semantic examples for each intent
        self.intent_examples = {
            'emergency': ['help me', 'i am in an accident', 'call an ambulance', 'call the police', 'sos', 'crash', 'injured'],
            'first_aid': ['im bleeding', 'how to treat a burn', 'cpr', 'choking', 'first aid', 'wound', 'unconscious', 'broken bone'],
            'challan': ['traffic challan', 'speeding ticket', 'no helmet fine', 'seatbelt penalty', 'drunk driving', 'licence suspended'],
            'legal': ['motor vehicles act', 'what are my rights', 'legal inspection', 'traffic laws', 'mva section'],
            'road_weather': ['is it raining', 'flood on the road', 'fog visibility', 'heatwave', 'storm coming', 'monsoon'],
            'safe_route': ['navigate to', 'safest route', 'directions to', 'best way to get to', 'avoid bad roads'],
            'road_infrastructure': ['who maintains this road', 'road authority', 'pwd', 'nhai', 'contractor', 'report to authorities'],
            'road_issue': ['pothole here', 'road is damaged', 'hazard on road', 'debris block', 'bad road condition'],
        }
        
        # Precompute embeddings for examples
        self.intent_embeddings = []
        for intent, examples in self.intent_examples.items():
            embs = self.embedding_function(examples)
            for emb in embs:
                self.intent_embeddings.append((intent, emb))
                
    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = sum(a * a for a in v1) ** 0.5
        norm_b = sum(b * b for b in v2) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def detect(self, message: str) -> str:
        text = message.lower()
        
        # Fast paths for critical or highly specific terms
        if _has_any(text, ('accident', 'ambulance', 'hospital', 'police', 'emergency', 'sos', 'crash', 'injured', 'help me')):
            return 'emergency'
            
        if _has_any(text, ('first aid', 'cpr', 'bleeding', 'choking', 'burn', 'wound', 'unconscious')):
            return 'first_aid'
            
        if CHALLAN_CODE_PATTERN.search(message) or _has_any(text, ('challan', 'fine', 'penalty', 'ticket')):
            return 'challan'
            
        if _has_any(text, ('legal', 'rights', 'section', 'laws')) or re.search(r'\bact\b', text):
            return 'legal'
            
        if _has_any(text, ('weather', 'rain', 'fog', 'flood', 'monsoon')):
            return 'road_weather'
            
        if _has_any(text, ('route', 'navigate', 'directions', 'way to')):
            return 'safe_route'
            
        if _has_any(text, ('who maintains', 'contractor', 'nhai', 'pwd', 'authority')):
            return 'road_infrastructure'
            
        if _has_any(text, ('pothole', 'hazard', 'debris', 'damaged')):
            return 'road_issue'
            
        # Semantic Routing Fallback
        query_emb = self.embedding_function([message])[0]
        
        best_intent = 'general'
        best_score = 0.55 # Threshold
        
        for intent, emb in self.intent_embeddings:
            score = self._cosine_similarity(query_emb, emb)
            if score > best_score:
                best_score = score
                best_intent = intent
                
        return best_intent

    def refine_intent(
        self,
        initial_intent: str,
        message: str,
        history: list[dict[str, Any]],
    ) -> str:
        if initial_intent != 'general':
            return initial_intent

        if not history:
            return initial_intent

        text = message.lower().strip()
        is_short = len(text.split()) <= _AMBIGUOUS_SHORT_MESSAGE_THRESHOLD
        is_follow_up = _has_any(text, _FOLLOW_UP_INDICATORS)

        if not is_short and not is_follow_up:
            return initial_intent

        previous_intents = []
        for msg in reversed(history):
            meta = msg.get("metadata")
            if isinstance(meta, dict):
                intent = meta.get("intent")
                if intent and intent != 'general' and intent != 'blocked':
                    previous_intents.append(intent)

        if not previous_intents:
            return initial_intent

        most_recent_intent = previous_intents[0]
        logger = __import__('logging').getLogger("safevixai.chatbot.intent")
        logger.info(
            "Refined intent '%s' -> '%s' from history (msg='%s', short=%s, follow_up=%s)",
            initial_intent, most_recent_intent, message[:50], is_short, is_follow_up,
        )
        return most_recent_intent
