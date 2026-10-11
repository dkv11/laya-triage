from app.triage import triage

TESTS = [
    ("motor se jalne ki smell aa rahi hai", "2026-10-10 08:10:00"),
    ("flow meter same reading dikha raha hai", "2026-10-10 21:00:00"),
    ("pump se thodi awaaz aa rahi hai", "2026-10-10 11:00:00"),
]

for text, at_time in TESTS:
    result = triage(text, at_time, operator_name="Ramesh")
    print(f"\n>>> [{at_time}] {text}")
    print(f"    → {result['asset_id']} | {result['team']} | {result['issue_type']} | priority {result['priority']}")
    for line in result["reason"]:
        print(f"      • {line}")
    print(f"    First check: {result['first_checks'][0]}")
    print(f"    Saved: message #{result['message_id']}, decision #{result['decision_id']}")
