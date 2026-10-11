import json
import os

from app.laya_model import get_router

THRESHOLD = 0.5
TEST_FILES = ["data/test_synthetic.jsonl", "data/test_real.jsonl"]


def is_correct(answer, qtype, expected):
    if qtype == "noul":
        return (answer["noul"] >= 0.5) == expected
    return answer["choice"] == expected


router = get_router()
print(f"Model: {os.environ.get('LAYA_CHECKPOINT') or 'base laya-multilingual (zero-shot)'}\n")

for path in TEST_FILES:
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    scores = {}            # question -> [correct, total]
    team = []              # (confidence, correct) for the team question
    for row in rows:
        answers = router.predict(row["state"], row["questions"], model="multilingual")["answers"]
        for question, expected in row["expected"].items():
            ok = is_correct(answers[question], row["questions"][question]["type"], expected)
            scores.setdefault(question, [0, 0])
            scores[question][0] += ok
            scores[question][1] += 1
            if question == "team":
                team.append((answers[question]["confidence"], ok))

    print(f"=== {path} ({len(rows)} messages) ===")
    for question, (correct, total) in scores.items():
        print(f"  {question:<11} accuracy {correct}/{total} = {correct / total:.0%}")

    handled = [ok for conf, ok in team if conf >= THRESHOLD]
    right_conf = [conf for conf, ok in team if ok]
    wrong_conf = [conf for conf, ok in team if not ok]
    print(f"  Laya would handle {len(handled)}/{len(team)} = {len(handled) / len(team):.0%} "
          f"(confidence >= {THRESHOLD}), accuracy on those: "
          f"{sum(handled)}/{len(handled) or 1}")
    if right_conf:
        print(f"  avg confidence when right: {sum(right_conf) / len(right_conf):.2f}")
    if wrong_conf:
        print(f"  avg confidence when wrong: {sum(wrong_conf) / len(wrong_conf):.2f}")
    for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        h = [ok for conf, ok in team if conf >= t]
        print(f"  threshold {t}: Laya handles {len(h)}/{len(team)}, right on {sum(h)}/{len(h) or 1}")

    print()
