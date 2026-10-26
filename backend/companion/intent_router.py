"""Optional Gemini intent recognition. It never computes energy or returns advice.

The model may select ONE safe, predefined tool intent. Python then constructs
EVERY numerical fact from the validated calculation engines. Unknown response,
timeout, malformed output or no key => deterministic local fallback.
"""
from __future__ import annotations
import json
import os
import httpx

INTENT_PROMPTS = {
    'score_why': 'Explain my score calculation',
    'recommendation_challenge': 'Why recommend this upgrade?',
    'carbon_why': 'How is my carbon calculated?',
    'property_value': 'What is the evidence for my house value?',
    'household_habits': 'What are safe daily habits for recycling and kitchen waste?',
    'budget': 'What is the best upgrade within my current budget?',
    'model_evidence': 'How accurate is the real-world ML validation?',
}


def route_gemini_intent(question: str) -> str | None:
    """Returns a permitted *label only*, never trusts model-generated numbers."""
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key: return None
    model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    prompt = (
        'Classify the homeowner question for TREE. Return EXACTLY one JSON object '
        'with a single key "intent". Choose one of: '
        + ', '.join(INTENT_PROMPTS) + ', none. '
        'Do not answer the homeowner. Do not invent or return facts, figures or retrofit labels. '
        'Use none for unrelated topics or unsupported calculations.\nQUESTION:\n'
        + question[:2000]
    )
    try:
        with httpx.Client(timeout=7) as client:
            response = client.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                params={'key': key},
                json={'contents':[{'parts':[{'text':prompt}]}],
                      'generationConfig':{'temperature':0,'responseMimeType':'application/json'}})
            response.raise_for_status()
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
        intent = json.loads(text).get('intent')
        return intent if intent in INTENT_PROMPTS else None
    except (httpx.HTTPError, KeyError, ValueError, IndexError, TypeError):
        return None
