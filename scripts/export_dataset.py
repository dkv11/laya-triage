import json

from app.db import get_connection
from app.laya_model import QUESTIONS
from app.llm import validate_extraction
from app.triage import LAYA_MODEL_NAME

OUT_PATH = "data/laya_dataset.jsonl"

QUERY = """
    SELECT d.id, m.text, d.team, d.model, d.raw_output, f.is_correct
    FROM decisions d
    JOIN operator_messages m ON m.id = d.message_id
    LEFT JOIN feedback f ON f.decision_id = d.id
    ORDER BY d.id
"""


def message_labels(model, raw_output):
    """What the MESSAGE itself says: team hint, asset, is_problem."""
    data = json.loads(raw_output)
    if model != LAYA_MODEL_NAME:
        data = validate_extraction(data)
    return data["team_hint"], data["asset_id"], data["is_problem"]


def normalise(text):                                            # NEW
    """Same message despite different spacing or capitals."""
    return " ".join(text.lower().split())


with get_connection() as conn:
    rows = conn.execute(QUERY).fetchall()

examples = {}                                                   # NEW: normalised text -> example
skipped = {"correction": 0, "laya_unreviewed": 0, "duplicate": 0}

for row in rows:
    team_hint, asset_id, is_problem = message_labels(row["model"], row["raw_output"])

    if row["is_correct"] == 0:
        skipped["correction"] += 1
        continue
    if row["is_correct"] == 1 and row["team"] == team_hint:
        source = "engineer"
    elif row["model"] != LAYA_MODEL_NAME:
        source = "teacher"
    else:
        skipped["laya_unreviewed"] += 1
        continue

    expected = {"team": team_hint, "asset": asset_id or "none"}
    if row["model"] != LAYA_MODEL_NAME:                         # NEW
        expected["is_problem"] = is_problem   # Laya's own is_problem guess was never shown to the engineer

    key = normalise(row["text"])                                # NEW: keep one example per message,
    if key in examples:                                         #      preferring an engineer label
        skipped["duplicate"] += 1
        if examples[key]["meta"]["source"] == "engineer":
            continue

    examples[key] = {
        "state": row["text"],
        "questions": QUESTIONS,
        "expected": expected,
        "meta": {"decision_id": row["id"], "source": source},
    }

with open(OUT_PATH, "w", encoding="utf-8") as out:
    for example in examples.values():
        out.write(json.dumps(example, ensure_ascii=False) + "\n")

sources = [e["meta"]["source"] for e in examples.values()]
print(f"Wrote {len(examples)} examples to {OUT_PATH}")
print(f"  engineer: {sources.count('engineer')}, teacher: {sources.count('teacher')}")
print(f"  skipped: {skipped}")
