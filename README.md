# EQL Exam Trainer — Fitness Trainer Level 3

Adaptive practice for the Fitness Trainer Level 3 (EQF/EREPS) theory exam.

- **715 questions** in 8 topics: 71 from the official portal (practice exam + lesson quizzes), 334 based on the course lessons and the on-demand course book (all 9 modules), 50 from a Copilot-generated mock exam, the rest written for this bank
- **Mock exam**: 50 questions, 30 minutes, pass at 67% (real exam: 40 of 60)
- Feedback after each answer, with an explanation in English, plus Spanish when you answer wrong
- **Adaptive**: weak topics and missed questions come back more often; missed questions are asked again a few questions later
- Each person picks their name and a 4–6 digit PIN; progress is stored in Supabase

## How it fits together

| Part | What it does |
|---|---|
| `index.html` | The whole app (plain HTML/CSS/JS, no build step) |
| `questions.json` | The question bank (source of truth) |
| `config.js` | Supabase URL + publishable key (public by design) |
| `netlify.toml` | Netlify settings: publish the repo root, no build |
| `supabase/migrations/` | Database schema, already applied to the Supabase project |
| `scripts/check_questions.py` | Validates `questions.json` and exports `EQL_question_bank.csv` |

**Hosting:** Netlify site `eql-exam-trainer`, auto-deploys every push to `main`.
**Database:** Supabase project `eql-exam-trainer` (region eu-central-1).

## Security model

The `eql_users` table has row level security on and no policies, so the public key cannot read or write it directly.
The app only calls four functions: `eql_list_names`, `eql_register`, `eql_login`, `eql_save`.
PINs are stored as bcrypt hashes. After 5 wrong PINs a name is locked for 15 minutes.
This is fine for study progress. Don't reuse a PIN that protects anything important.

## Adding or fixing questions

1. Edit `questions.json`. Each question looks like:
   ```json
   {"id":"nut035","t":"nutrition","q":"Question text?","o":["A","B","C","D"],"a":2,
    "e":"English explanation","s":"Explicación en español"}
   ```
   `a` is the position of the right answer (0 = A, 1 = B, 2 = C, 3 = D). Questions can have 2–4 options (true/false questions use `["Niet waar (False)","Waar (True)"]`). Options are shuffled in the app, except for questions marked `"src":"portal"`, which keep the portal's order, and questions with `"fixed":true` (use it for 'All of the above' options). Add `"flag":"..."` to show a 'check this' note.
2. Run `python3 scripts/check_questions.py`
3. Commit and push. Netlify publishes it within a minute.

## Resetting someone's PIN

In the Supabase SQL editor:
```sql
update public.eql_users
set pin_hash = extensions.crypt('1234', extensions.gen_salt('bf', 8)), failed_attempts = 0, locked_until = null
where lower(name) = lower('Name');
```
