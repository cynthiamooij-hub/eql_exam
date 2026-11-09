"""Validate questions.json and export it to a CSV you can open in Excel.

Run:  python3 scripts/check_questions.py
Each question: id, t (topic), q, o (2-4 options), a (index of the correct option, 0 = A),
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
    opts = q.get("o", [])
    if not 2 <= len(opts) <= 4 or len(set(opts)) != len(opts): problems.append(f"{tag}: needs 2-4 different options")
    if not isinstance(q.get("a"), int) or not 0 <= q["a"] < len(opts): problems.append(f"{tag}: answer index out of range")
    for k in ("q", "e", "s"):
        if not q.get(k): problems.append(f"{tag}: missing {k}")
if problems:
    print("\n".join(problems)); sys.exit(1)

with open(ROOT / "EQL_question_bank.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Topic", "Source", "Question", "A", "B", "C", "D", "Correct", "Explanation (EN)", "Explicación (ES)", "Note"])
    for q in qs:
        w.writerow([q["id"], TOPICS[q["t"]], {"portal": "Official portal", "copilot": "Copilot mock exam"}.get(q.get("src"), "Mock bank"), q["q"], *(q["o"] + [""] * (4 - len(q["o"]))),
                    "ABCD"[q["a"]], q["e"], q["s"], q.get("flag", "")])
print(f"OK: {len(qs)} questions", dict(collections.Counter(TOPICS[q['t']] for q in qs)))
