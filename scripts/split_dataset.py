import json
import random
from collections import defaultdict

TEST_FRACTION = 0.2
random.seed(42)


def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalise(text):
    return " ".join(text.lower().split())


real = read("data/laya_dataset.jsonl")
real_texts = {normalise(r["state"]) for r in real}

by_situation = defaultdict(list)
for row in read("data/synthetic.jsonl"):
    if normalise(row["state"]) in real_texts:
        continue                      # never let a real test message leak into training
    by_situation[row["meta"]["situation"]].append(row)

train, test = [], []
for rows in by_situation.values():
    random.shuffle(rows)
    n_test = max(1, round(len(rows) * TEST_FRACTION))
    test += rows[:n_test]
    train += rows[n_test:]

write("data/train.jsonl", train)
write("data/test_synthetic.jsonl", test)
write("data/test_real.jsonl", real)
print(f"train: {len(train)}   test_synthetic: {len(test)}   test_real: {len(real)}")
