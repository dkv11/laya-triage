import time

from app.laya_model import classify_message
from app.llm import extract_message

MESSAGES = [
    ("P-101 se bahut awaaz aa rahi hai aur garam bhi ho raha hai", "mechanical"),
    ("motor se jalne ki smell aa rahi hai", "electrical"),
    ("flow meter 2 ghante se same reading dikha raha hai", "instrumentation"),
    ("blower trip ho gaya, MCB gir gaya", "electrical"),
    ("pump ke neeche paani leak ho raha hai", "mechanical"),
    ("sab theek hai, routine round done", "unknown"),
    ("blower se chingari nikal rahi hai", "electrical"),
]

laya_correct = qwen_correct = 0
for text, expected in MESSAGES:
    t = time.time(); laya = classify_message(text); laya_ms = (time.time() - t) * 1000
    t = time.time(); qwen, _ = extract_message(text); qwen_ms = (time.time() - t) * 1000
    laya_correct += laya["team_hint"] == expected
    qwen_correct += qwen["team_hint"] == expected
    print(f"\n{text}\n  expected {expected}")
    print(f"  Laya: {laya['team_hint']:<16} conf {laya['confidence']:.2f}  asset {laya['asset_id']}  safety {laya['safety_risk']}  {laya_ms:.0f} ms")
    print(f"  Qwen: {qwen['team_hint']:<16}            asset {qwen['asset_id']}  safety {qwen['safety_risk']}  {qwen_ms:.0f} ms")

print(f"\nTeam accuracy: Laya {laya_correct}/{len(MESSAGES)}, Qwen {qwen_correct}/{len(MESSAGES)}")
