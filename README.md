# FocusFlow

A study helper that suggests which task to work on now and for how long, based on deadlines, work left, difficulty and how much energy the student has. It explains each suggestion and learns, carefully, from what the student skips or starts.

Submitted release: **`v1.0-a2`**.

## Project status

| Part | Status |
| --- | --- |
| Recommendation engine (`focusflow/engine.py`): scoring, reasons, learning, close-call and learning-status notes, reset, 14-day deletion, export | Implemented, covered by 14 tests |
| Streamlit interface (`app.py`): add tasks, energy slider, suggestion with reason, Start / Not now / choose another / minutes slider, settings sidebar | Implemented |
| Scripted sessions (`replay.py`) | Implemented; replays three user scenarios without the interface |
| Local storage (`data/state.json`) | Implemented; single user, one device |
| Telling users when learning changes their suggestions (Amershi G18) | Planned |
| Calendar import, reminders, multi-device sync | Planned |
| Evaluation with real users | Not done yet |

## Technology stack

- **Python 3.11+**: all logic.
- **Streamlit**: the interface. Chosen because it turns Python into a working web page quickly, so time went into the interaction, not front-end code.
- **pytest**: tests for the engine.
- **"AI" approach**: a hand-weighted scoring model plus simple preference learning (capped weights per time of day and difficulty). No machine-learning library or external AI model is used. This keeps every suggestion explainable in one sentence. Undecided: whether to learn the score weights from data once there are real users.
- **AI tool used in development**: Claude (Anthropic), see below.

## Running or inspecting the work

```bash
pip install -r requirements.txt
streamlit run app.py        # opens the app in your browser
python replay.py            # replays three scripted sessions in the terminal
python -m pytest -q         # runs the tests
```

`replay_output.txt` holds the replay output for the submitted release, so you can inspect behaviour without installing anything. Your data is saved in `data/state.json`; delete it to start again.

## Development record

**v1: deadline-only** ([924845f](../../commit/924845f))
- Suggested the task with the nearest deadline, always for 45 minutes.
- Checked with three sample tasks: it suggested the hardest task at energy 5, 3 and 1 alike, with no reason shown. This ignored the student's state and gave no way to understand or correct it.

**v2: energy, reasons, correction, learning** ([bdb9009](../../commit/bdb9009))
- Score = 0.65 × urgency + 0.35 × fit between difficulty and energy + a learned preference.
- Each suggestion shows a plain reason; the user can start, skip, pick another task or change the minutes.
- The first replay showed two problems, both fixed in this commit:
  - A 4-hour task due the next day was never suggested, because energy fit outweighed a distant-looking deadline. Fix: urgency also counts work left per remaining day.
  - One skip pushed that urgent task below a 10-minute leftover. Fix: learning is weakened as a task becomes urgent, and the reason says "too urgent to move down".

**v3: guideline review and privacy** ([a451f47](../../commit/a451f47))
- After checking the project against Amershi et al. (2019) in Week 7:
  - G2: "Still learning (n of 10 choices)" note, and "Close call" when two tasks score almost the same.
  - G17: "Learn from my choices" switch (nothing is stored when off) and "Reset learning history" with a confirmation.
- Privacy: choice records and energy ratings are deleted after 14 days; export contains tasks, preferences in plain words and counts only. Mouse and typing are not recorded, because the Week 7 activity rule flagged between 83 and 195 of the same 1,039 intervals depending only on its settings.
- Checked with new tests and replay scenario C.

## AI assistance

- **Tool**: Claude (Anthropic), in the Claude app.
- **What I asked for**: help to choose a project scope, write the engine, interface, tests and replay script in stages, and draft this README and the report.
- **How suggestions were used or changed**: the first scoring formula hid urgent tasks; the replay exposed this and the formula was changed (see v2). A test written for the export was wrong (it checked the export time instead of record times) and was corrected.
- **How results were checked**: all 14 tests pass; replay output read line by line against the intended behaviour; reference details checked against publisher or library pages.
- **My own checks**: run the Streamlit app and check whole app can .

## Additional files

- `replay_output.txt`: output of `python replay.py` for the submitted release.
- The report is submitted separately and links to this repository. No ZIP file.
