VIBRATION_WARNING = 4.5 # mm/s, ISO 10816 class II
VIBRATION_ALARM = 7.1
PHASE_IMBALANCE_WARNING = 5 # percent
PHASE_IMBALANCE_ALARM = 10 # percent
STUCK_MIN_READINGS = 5
MIN_RUNNING_CURRENT = 1 # A, below this the motor is considered off

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

def check_phase_imbalance(df,baseline):
    """Phase imbalance: R phase current rises, B phase drops, motor heats up."""
    r = df["current_r_a"].mean()
    y = df["current_y_a"].mean()
    b = df["current_b_a"].mean()
    avg_current = (r + y + b) / 3

    max_dev = max(abs(r - avg_current), abs(y - avg_current), abs(b - avg_current))

    imbalance = max_dev / avg_current * 100

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
