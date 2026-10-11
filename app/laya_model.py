from dotenv import load_dotenv
load_dotenv()
from laya import Router

from app.config import ASSETS

SAFETY_WORDS = ["jalne", "jal raha", "jal gaya", "burn", "smoke", "dhuan", "dhua", "aag", "fire",
                "chingari", "spark", "shock", "current laga", "chot", "injur",
                "धुआं", "आग", "जलने", "चिंगारी"]

QUESTIONS = {
    "team": {
        "type": "choice",
        "instructions": "Which maintenance team should handle this equipment problem?",
        "criteria": {
            "mechanical": "noise, vibration, leakage, bearing, belt, coupling, seal",
            "electrical": "tripping, burning smell, sparks, current, voltage, MCB, cable, motor winding",
            "instrumentation": "a sensor, meter, transmitter or display shows a wrong, frozen or missing reading",
            "unknown": "not enough information, or everything is normal",
        },
    },
    "asset": {
        "type": "choice",
        "instructions": "Which machine is the message about?",
        "criteria": {**{a: f"the {info['type']} ({a})" for a, info in ASSETS.items()},
                     "none": "no machine is named or it is unclear"},
    },
    "is_problem": {"type": "noul", "instructions": "Does the message report a problem or abnormal condition?"},
}

_router = None


def get_router():
    """Load Laya once, on first use (loading takes seconds; predicting takes milliseconds)."""
    global _router
    if _router is None:
        _router = Router()
    return _router


def classify_message(text):
    """Laya's fast local answer, in the same shape as llm.extract_message, plus confidence."""
    answers = get_router().predict(text, QUESTIONS, model="multilingual")["answers"]
    lower = text.lower()
    asset = answers["asset"]["choice"]
    return {
        "asset_id": None if asset == "none" else asset,
        "team_hint": answers["team"]["choice"],
        "safety_risk": any(word in lower for word in SAFETY_WORDS),
        "is_problem": answers["is_problem"]["noul"] >= 0.5,
        "confidence": answers["team"]["confidence"],
        "summary_en": text,
    }
