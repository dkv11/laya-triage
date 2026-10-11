import numpy as np

VIBRATION_WARNING = 4.5 # mm/s, ISO 10816 class II
VIBRATION_ALARM = 7.1
PHASE_IMBALANCE_WATCH = 3 # percent; ~2x the healthy max measured by scripts/imbalance_noise.py
PHASE_IMBALANCE_WARNING = 5 # percent
PHASE_IMBALANCE_ALARM = 10 # percent
STUCK_MIN_READINGS = 10
MIN_RUNNING_CURRENT = 1 # A, below this the motor is considered off
VIBRATION_RISE_WATCH = 25 # percent above the machine's normal vibration


def check_bearing_wear(df,baseline):
    """High vibration = mechanical problem. Temperature rise is supporting evidence."""
    vib = df["vibration_mm_s"].mean()
    temp_rise = df["bearing_temp_c"].mean() - baseline["bearing_temp"]

    if vib <= VIBRATION_WARNING:
        return None

    severity = "alarm" if vib > VIBRATION_ALARM else "warning"
    return {
        "rule": "bearing_wear",
        "team": "mechanical",
        "severity": severity,
        "evidence": f"avg vibration {vib:.2f} mm/s (limit {VIBRATION_WARNING}), "f"bearing temp {temp_rise:+.1f} °C vs normal",
    }

def phase_imbalance_pct(r, y, b):
    """Max deviation of any phase from the average, as % of the average.
    Works on single numbers or whole pandas columns."""
    avg = (r + y + b) / 3
    max_dev = np.maximum.reduce([abs(r - avg), abs(y - avg), abs(b - avg)])
    return max_dev / avg * 100


def check_phase_imbalance(df,baseline):
    """Phase imbalance: R phase current rises, B phase drops, motor heats up."""
    r = df["current_r_a"].mean()
    y = df["current_y_a"].mean()
    b = df["current_b_a"].mean()
    imbalance = phase_imbalance_pct(r, y, b)

    if imbalance <= PHASE_IMBALANCE_WARNING:
        return None

    severity = "alarm" if imbalance > PHASE_IMBALANCE_ALARM else "warning"

    return {
        "rule": "phase_imbalance",
        "team": "electrical",
        "severity": severity,
        "evidence": f"phase imbalance {imbalance:.1f}% (limit {PHASE_IMBALANCE_WARNING}%), "f"phase currents R:{r:.1f}A, Y:{y:.1f}A, B:{b:.1f}A",
    }

def check_flow_sensor_stuck(df, baseline):
    """Instrumentation: flow reading frozen while the motor is running."""
    if len(df) < STUCK_MIN_READINGS:
        return None                      # not enough data to judge
    if df["flow_m3h"].nunique() > 1:
        return None                      # value is moving: sensor alive
    current = df["current_r_a"].mean()
    if current < MIN_RUNNING_CURRENT:
        return None                      # machine is off: flat flow is normal

    return {
        "rule": "flow_sensor_stuck",
        "team": "instrumentation",
        "severity": "warning",
        "evidence": f"flow frozen at {df['flow_m3h'].iloc[0]} m3/h for {len(df)} readings "
                    f"while motor draws {current:.1f} A",
    }

def check_vibration_rising(df, baseline):
    """Mechanical early warning: vibration well above this machine's normal, but below the ISO warning limit."""

    vib = df["vibration_mm_s"].mean()
    rise_pct = (vib - baseline["vibration"]) / baseline["vibration"] * 100
    if rise_pct <= VIBRATION_RISE_WATCH:
        return None
    if vib > VIBRATION_WARNING:
        return None  # already caught by check_bearing_wear, no need to duplicate
    return {
        "rule": "vibration_rising",
        "team": "mechanical",
        "severity": "watch",
        "evidence": f"vibration {vib:.2f}mm/s is rising {rise_pct:.1f}% above normal {baseline['vibration']:.2f}mm/s",
    }


def check_imbalance_rising(df, baseline):
    """Electrical early warning: phase imbalance above the healthy noise floor, but below the warning limit."""
    r = df["current_r_a"].mean()
    y = df["current_y_a"].mean()
    b = df["current_b_a"].mean()
    imbalance = phase_imbalance_pct(r, y, b)

    if imbalance <= PHASE_IMBALANCE_WATCH:
        return None
    if imbalance > PHASE_IMBALANCE_WARNING:
        return None  # already caught by check_phase_imbalance, no need to duplicate
    return {
        "rule": "imbalance_rising",
        "team": "electrical",
        "severity": "watch",
        "evidence": f"phase imbalance {imbalance:.2f}% is above healthy level (watch {PHASE_IMBALANCE_WATCH}%), "
                    f"phase currents R:{r:.1f}A, Y:{y:.1f}A, B:{b:.1f}A",
    }


RULES = [
    check_bearing_wear,
    check_vibration_rising,
    check_phase_imbalance,
    check_imbalance_rising,
    check_flow_sensor_stuck,
]


def run_rules(df, baseline):
    """Run every rule on one window. Returns a list of findings (empty list = healthy)."""
    findings = []
    for rule in RULES:
        finding = rule(df, baseline)
        if finding is not None:
            findings.append(finding)
    return findings



    