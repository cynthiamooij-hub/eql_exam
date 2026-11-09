"""Validate questions.json and export it to a CSV you can open in Excel.

Run:  python3 scripts/check_questions.py
Each question: id, t (topic), q, o (4 options), a (index of correct option 0-3),
e (English explanation), s (Spanish explanation), optional src="portal", optional flag.
"""
import collections, csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = {"anatomy": "Anatomy", "physiology": "Exercise physiology", "biomechanics": "Biomechanics",
          "training": "Training principles", "nutrition": "Nutrition", "safety": "Health & safety",
          "intake": "Intake & testing", "coaching": "Coaching & behaviour change"}

qs = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
problems = []
ids = collections.Counter(q.get("id") for q in qs)
for q in qs:
    tag = q.get("id", "?")
    if ids[tag] > 1: problems.append(f"{tag}: duplicate id")
    if q.get("t") not in TOPICS: problems.append(f"{tag}: unknown topic {q.get('t')}")
    if len(q.get("o", [])) != 4 or len(set(q["o"])) != 4: problems.append(f"{tag}: needs 4 different options")
    if q.get("a") not in (0, 1, 2, 3): problems.append(f"{tag}: answer index must be 0-3")
    for k in ("q", "e", "s"):
        if not q.get(k): problems.append(f"{tag}: missing {k}")
if problems:
    print("\n".join(problems)); sys.exit(1)

with open(ROOT / "EQL_question_bank.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Topic", "Source", "Question", "A", "B", "C", "D", "Correct", "Explanation (EN)", "Explicación (ES)", "Note"])
    for q in qs:
        w.writerow([q["id"], TOPICS[q["t"]], "Official practice exam" if q.get("src") else "Mock bank", q["q"], *q["o"],
                    "ABCD"[q["a"]], q["e"], q["s"], q.get("flag", "")])
print(f"OK: {len(qs)} questions", dict(collections.Counter(TOPICS[q['t']] for q in qs)))
