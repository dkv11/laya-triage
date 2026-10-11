import json
import random

from app.config import ASSETS
from app.laya_model import QUESTIONS
from app.llm import MODEL, client, extract_message

OUT_PATH = "data/synthetic.jsonl"
PER_CALL = 6
QUICK_TEST = False        # True = only the first 2 situations; set False for the full run

random.seed(7)

# (team, is_problem, situation) - the label comes from here, not from a model
SCENARIOS = [
    ("mechanical", True, "loud abnormal noise or grinding sound from the machine"),
    ("mechanical", True, "the machine is shaking or vibrating much more than usual"),
    ("mechanical", True, "water or oil leaking from the seal or gland"),
    ("mechanical", True, "the bearing area is too hot to touch"),
    ("mechanical", True, "belt slipping or coupling looks loose"),
    ("mechanical", True, "foundation bolts are loose and the base is moving"),
    ("electrical", True, "burning smell coming from the motor"),
    ("electrical", True, "sparks seen at the panel or starter"),
    ("electrical", True, "MCB or overload relay keeps tripping"),
    ("electrical", True, "motor is humming but not starting"),
    ("electrical", True, "cable or terminal is heating up or has melted insulation"),
    ("mechanical", True, "the motor bearing is very hot or noisy"),
    ("mechanical", True, "the motor and pump are shaking because the base or bolts are loose"),
    ("instrumentation", True, "the motor is running fine but a reading on the screen is wrong or jumping"),
    ("electrical", True, "the panel or starter has a burning smell, nothing about the motor itself"),

    ("electrical", True, "the motor body feels like it gives a mild electric shock"),
    ("instrumentation", True, "the flow reading is stuck at the same value for hours"),
    ("instrumentation", True, "the pressure gauge shows zero even though the machine is running"),
    ("instrumentation", True, "a reading on the screen keeps jumping up and down randomly"),
    ("instrumentation", True, "the SCADA screen shows no data or communication failure for a tag"),
    ("instrumentation", True, "the local meter and the screen show very different values"),
    ("unknown", True, "something seems wrong but the operator gives no details"),
    ("unknown", False, "routine round done, everything is running normally"),
]

ASSET_STYLES = ["tag", "type", "none"]

SYSTEM = "You write realistic messages that plant operators in India send to the maintenance team on WhatsApp."


def asset_instruction(style, asset_id):
    if style == "tag":
        return f"Mention the machine by its tag {asset_id}."
    if style == "type":
        return f"Call it the {ASSETS[asset_id]['type']}, without any tag number."
    return "Do not say which machine: no tag, and do not say pump or blower. You may say 'motor' or 'machine'."


def generate(situation, style, asset_id):
    """Ask the teacher for PER_CALL different ways an operator might report this situation."""
    prompt = f"""Write {PER_CALL} different messages from operators about this situation: {situation}.
{asset_instruction(style, asset_id)}
Write 3 in Hinglish (Hindi in Roman letters), 2 in Hindi (Devanagari script) and 1 in simple English.
Make them realistic: short, informal, different wording each time, some with spelling mistakes.
Never use the words mechanical, electrical or instrumentation.
Return JSON: {{"messages": ["...", "..."]}}"""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.9,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    )
    data = json.loads(response.choices[0].message.content or "{}")
    return [m.strip() for m in data.get("messages", []) if isinstance(m, str) and len(m.strip()) >= 2]


def passes_check(text, team, asset, is_problem):
    """Second opinion: reading ONLY the text, does the teacher reach the intended labels?"""
    try:
        data, _ = extract_message(text)
    except ValueError:
        return False
    return (data["team_hint"] == team
            and (data["asset_id"] or "none") == asset
            and data["is_problem"] == is_problem)


if __name__ == "__main__":
    scenarios = SCENARIOS[:2] if QUICK_TEST else SCENARIOS
    kept, rejected, seen = [], [], set()

    for team, is_problem, situation in scenarios:
        for style in ASSET_STYLES:
            asset_id = random.choice(list(ASSETS))
            asset = "none" if style == "none" else asset_id
            for text in generate(situation, style, asset_id):
                key = " ".join(text.lower().split())
                if key in seen:
                    continue
                seen.add(key)
                if passes_check(text, team, asset, is_problem):
                    kept.append({
                        "state": text,
                        "questions": QUESTIONS,
                        "expected": {"team": team, "asset": asset, "is_problem": is_problem},
                        "meta": {"source": "synthetic", "situation": situation, "asset_style": style},
                    })
                else:
                    rejected.append((text, team, asset))
        print(f"{situation[:55]:<55} kept so far: {len(kept)}")

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for example in kept:
            out.write(json.dumps(example, ensure_ascii=False) + "\n")

    total = len(kept) + len(rejected)
    print(f"\nKept {len(kept)} of {total} ({len(kept) / max(total, 1):.0%}) -> {OUT_PATH}")
    print("\nSome rejected messages (intended labels):")
    for text, team, asset in rejected[:10]:
        print(f"  [{team}, {asset}] {text}")
