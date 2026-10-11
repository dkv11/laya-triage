from app.llm import validate_extraction

GOOD = {
    "asset_id": "P-101", "symptoms": ["loud noise"], "team_hint": "mechanical",
    "safety_risk": False, "is_problem": True, "language": "hinglish",
    "summary_en": "Pump is noisy.",
}

CASES = [
    ("good output", GOOD, "accept"),
    ("team with capital letter", {**GOOD, "team_hint": "Electrical"}, "accept"),
    ("invented asset", {**GOOD, "asset_id": "P-102"}, "accept"),
    ("invalid team", {**GOOD, "team_hint": "plumber"}, "reject"),
    ("safety as text", {**GOOD, "safety_risk": "yes"}, "reject"),
    ("missing key", {k: v for k, v in GOOD.items() if k != "language"}, "reject"),
    ("not an object", ["a", "list"], "reject"),
]

for name, data, expected in CASES:
    try:
        result = validate_extraction(data)
        outcome = "accept"
        detail = f"team={result['team_hint']}, asset={result['asset_id']}"
    except ValueError as e:
        outcome = "reject"
        detail = str(e)
    status = "✅" if outcome == expected else "❌"
    print(f"{status} {name:<26} {outcome:<7} {detail}")
