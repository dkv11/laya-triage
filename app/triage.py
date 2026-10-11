from app.config import ASSETS
from app.db import get_recent_readings, save_decision, save_message
from app.llm import MODEL, extract_message
from app.rules import run_rules
from app.laya_model import classify_message
import json

SNAPSHOT_COLUMNS = ["vibration_mm_s", "bearing_temp_c", "current_r_a", "current_y_a",
                    "current_b_a", "flow_m3h", "pressure_bar"]

LAYA_MODEL_NAME = "laya-multilingual"
LAYA_MIN_CONFIDENCE = 0.5   # below this, ask the LLM; tuned on scripts/compare_models.py, revisit with more data


SEVERITY_RANK = {"watch": 1, "warning": 2, "alarm": 3}

SAFETY_CHECKS = [
    "Stop the machine and isolate power (lock-out/tag-out) before inspection",
    "Keep people away until it is declared safe",
]

RULE_CHECKS = {
    "bearing_wear": [
        "Check bearing temperature with a handheld thermometer",
        "Listen for bearing noise with a stethoscope or screwdriver",
        "Check lubrication against the greasing schedule",
        "Check coupling alignment",
    ],
    "vibration_rising": [
        "Compare vibration over the last shift",
        "Check foundation bolts and coupling",
        "Plan a bearing inspection at the next stop",
    ],
    "phase_imbalance": [
        "Measure 3-phase voltage and current at the starter",
        "Check terminals for looseness or heat marks",
        "Check cable and fuses on the weak phase",
    ],
    "imbalance_rising": [
        "Check terminal tightness on the next round",
        "Log phase currents every hour",
    ],
    "flow_sensor_stuck": [
        "Compare with a local flow indicator or the pump curve",
        "Check transmitter power and signal cable",
        "Check PLC/SCADA communication for this tag",
    ],
}

TEAM_CHECKS = {
    "mechanical": ["Inspect for noise, vibration and leaks", "Check bearing temperature and lubrication"],
    "electrical": ["Check starter, MCB/overload and terminals", "Measure phase currents and voltages"],
    "instrumentation": ["Compare the reading with a local gauge", "Check sensor power, wiring and communication"],
    "unknown": ["Visit the machine and report what you see, hear and smell"],
}


def decide(extraction, findings_by_asset):
    """Combine the operator's message (LLM extraction) with sensor findings into one decision.
    findings_by_asset: {asset_id: [finding, ...]} at the time of the message."""
    hint = extraction["team_hint"]

    # 1. Which machine?
    asset_id = extraction["asset_id"]
    asset_from_sensors = False
    if asset_id is None:
        candidates = [a for a, fs in findings_by_asset.items() if fs]
        if hint != "unknown":
            matching = [a for a in candidates if any(f["team"] == hint for f in findings_by_asset[a])]
            if matching:
                candidates = matching
        if len(candidates) == 1:
            asset_id = candidates[0]
            asset_from_sensors = True

    findings = findings_by_asset.get(asset_id, []) if asset_id else []
    top = max(findings, key=lambda f: SEVERITY_RANK[f["severity"]], default=None)

    # 2. Which team?
    if top and top["severity"] in ("warning", "alarm"):
        team = top["team"]
    elif hint != "unknown":
        team = hint
    elif top:
        team = top["team"]
    else:
        team = "unknown"

    # 3. How urgent?
    if extraction["safety_risk"]:
        issue_type, priority = "emergency", 5
    elif top and top["severity"] == "alarm":
        issue_type, priority = "emergency", 4
    elif top and top["severity"] == "warning":
        issue_type, priority = "corrective", 3
    elif extraction["is_problem"] or top:
        issue_type, priority = "corrective", 2
    else:
        issue_type, priority = "routine", 1

    # 4. Why?
    reasons = [f"Operator: {extraction['summary_en']}"]
    if asset_from_sensors:
        reasons.append(f"Machine identified from sensor data: {asset_id}")
    for f in findings:
        reasons.append(f"Sensors ({f['severity']}): {f['evidence']}")
    if top and hint not in ("unknown", top["team"]):
        reasons.append(f"Note: operator's description suggests {hint}, sensors point to {top['team']}")
    if asset_id and extraction["is_problem"] and not findings:
        reasons.append("Sensors show nothing abnormal yet; relying on operator report")

    # 5. What to check first?
    checks = list(SAFETY_CHECKS) if extraction["safety_risk"] else []
    if top and top["team"] == team:
        checks += RULE_CHECKS[top["rule"]]
    else:
        checks += TEAM_CHECKS[team]

    return {
        "asset_id": asset_id,
        "team": team,
        "issue_type": issue_type,
        "priority": priority,
        "reason": reasons,
        "first_checks": checks,
    }

def sensor_snapshot(at_time):
    """For every machine: 10-minute averages and rule findings at this moment."""
    snapshot = {}
    for asset_id, baseline in ASSETS.items():
        df = get_recent_readings(asset_id, at_time)
        if df.empty:
            snapshot[asset_id] = {"averages": {}, "findings": []}
            continue
        snapshot[asset_id] = {
            "averages": df[SNAPSHOT_COLUMNS].mean().round(2).to_dict(),
            "findings": run_rules(df, baseline),
        }
    return snapshot

def understand_message(text):
    """System 1 (Laya, fast, local) first; System 2 (LLM) only when Laya isn't confident.
    Returns (extraction, model_used, raw_output)."""
    fast = classify_message(text)
    if fast["confidence"] >= LAYA_MIN_CONFIDENCE:
        return fast, LAYA_MODEL_NAME, json.dumps(fast)

    extraction, raw = extract_message(text)
    # The keyword guard rail always applies: never let a model "un-see" a burning smell
    extraction["safety_risk"] = extraction["safety_risk"] or fast["safety_risk"]
    return extraction, MODEL, raw


def triage(text, at_time, operator_name=None):
    """Full pipeline: sensors + LLM → decision → saved to the database."""
    snapshot = sensor_snapshot(at_time)
    extraction, model_used, raw = understand_message(text)


    findings_by_asset = {a: s["findings"] for a, s in snapshot.items()}
    decision = decide(extraction, findings_by_asset)

    message_id = save_message(text, extraction["asset_id"], operator_name, at_time)
    decision_id = save_decision(message_id, decision, snapshot, model_used, raw, at_time)

    return {"message_id": message_id, "decision_id": decision_id,"model": model_used, "extraction": extraction, **decision}

