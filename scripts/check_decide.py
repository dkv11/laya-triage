from app.triage import decide


def ext(**changes):
    """A normal 'problem' extraction, with some fields changed."""
    base = {"asset_id": None, "symptoms": [], "team_hint": "unknown", "safety_risk": False,
            "is_problem": True, "language": "hinglish", "summary_en": "test"}
    return {**base, **changes}


IMBALANCE_ALARM = {"rule": "phase_imbalance", "team": "electrical", "severity": "alarm", "evidence": "imbalance 18%"}
IMBALANCE_WARN = {"rule": "phase_imbalance", "team": "electrical", "severity": "warning", "evidence": "imbalance 7%"}
BEARING_WARN = {"rule": "bearing_wear", "team": "mechanical", "severity": "warning", "evidence": "vibration 5.8"}
FLOW_STUCK = {"rule": "flow_sensor_stuck", "team": "instrumentation", "severity": "warning", "evidence": "frozen 118.4"}

CASES = [
    # name, extraction, findings_by_asset, expected (asset, team, issue_type, priority)
    ("burning smell, no machine named",
     ext(team_hint="electrical", safety_risk=True),
     {"P-101": [], "B-201": [IMBALANCE_ALARM]},
     ("B-201", "electrical", "emergency", 5)),
    ("noise on P-101, sensors agree",
     ext(asset_id="P-101", team_hint="mechanical"),
     {"P-101": [BEARING_WARN], "B-201": []},
     ("P-101", "mechanical", "corrective", 3)),
    ("P-101 hot, sensors see nothing",
     ext(asset_id="P-101", team_hint="mechanical"),
     {"P-101": [], "B-201": []},
     ("P-101", "mechanical", "corrective", 2)),
    ("operator says noise, sensors say electrical",
     ext(asset_id="B-201", team_hint="mechanical"),
     {"P-101": [], "B-201": [IMBALANCE_WARN]},
     ("B-201", "electrical", "corrective", 3)),
    ("flow meter frozen, no machine named",
     ext(team_hint="instrumentation"),
     {"P-101": [FLOW_STUCK], "B-201": []},
     ("P-101", "instrumentation", "corrective", 3)),
    ("all fine",
     ext(is_problem=False),
     {"P-101": [], "B-201": []},
     (None, "unknown", "routine", 1)),
]

for name, extraction, findings, expected in CASES:
    d = decide(extraction, findings)
    got = (d["asset_id"], d["team"], d["issue_type"], d["priority"])
    print(f"{'✅' if got == expected else '❌'} {name}")
    if got != expected:
        print(f"     expected {expected}\n     got      {got}")

print("\nExample full decision (case 1):")
d = decide(CASES[0][1], CASES[0][2])
for key, value in d.items():
    print(f"  {key}: {value}")
