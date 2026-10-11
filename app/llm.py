import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.config import ASSETS
from app.prompts import build_extract_prompt

load_dotenv()

client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["OPENROUTER_API_KEY"])
MODEL = os.environ["LLM_MODEL"]

TEAMS = {"mechanical", "electrical", "instrumentation", "unknown"}
LANGUAGES = {"english", "hindi", "hinglish"}
REQUIRED_KEYS = {"asset_id", "symptoms", "team_hint", "safety_risk", "is_problem", "language", "summary_en"}


def validate_extraction(data):
    """Check the LLM's JSON and clean small mistakes. Raises ValueError if it can't be trusted."""
    if not isinstance(data, dict):
        raise ValueError("output is not a JSON object")

    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"missing keys: {missing}")

    team = str(data["team_hint"]).strip().lower()
    if team not in TEAMS:
        raise ValueError(f"invalid team_hint: {data['team_hint']!r}")

    language = str(data["language"]).strip().lower()
    if language not in LANGUAGES:
        raise ValueError(f"invalid language: {data['language']!r}")

    if not isinstance(data["safety_risk"], bool) or not isinstance(data["is_problem"], bool):
        raise ValueError("safety_risk and is_problem must be true or false")

    if not isinstance(data["symptoms"], list):
        raise ValueError("symptoms must be a list")

    asset_id = data["asset_id"]
    if asset_id not in ASSETS:
        asset_id = None   # unknown or invented asset: safer to say "not sure"

    return {
        "asset_id": asset_id,
        "symptoms": [str(s) for s in data["symptoms"]],
        "team_hint": team,
        "safety_risk": data["safety_risk"],
        "is_problem": data["is_problem"],
        "language": language,
        "summary_en": str(data["summary_en"]),
    }


def extract_message(text, retries=1):
    """Turn an operator message into validated structured data.
    Returns (data, raw_output). Raises ValueError if the LLM keeps returning bad output."""
    last_error = None
    for attempt in range(retries + 1):
        response = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_extract_prompt()},
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content
        try:
            return validate_extraction(json.loads(raw or "")), raw
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
    raise ValueError(f"LLM output invalid after {retries + 1} attempts: {last_error}")
