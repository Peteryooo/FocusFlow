"""Replay scripted FocusFlow sessions without the Streamlit interface.

Usage:  python replay.py
Shows each recommendation, the reason given, the user's scripted response
and how the learned preferences change. Uses the same engine as app.py.
"""
import json
from datetime import datetime, timedelta

from focusflow import engine

START = datetime(2026, 11, 16, 9, 0)  # Monday


def make_state() -> engine.State:
    return engine.State(tasks=[
        engine.Task("Statistics assignment", START + timedelta(days=4, hours=14), 4.0, 5, id="stats"),
        engine.Task("Read HCI chapter 3", START + timedelta(days=6), 1.5, 2, id="hci"),
        engine.Task("Spanish vocabulary", START + timedelta(days=9), 1.0, 1, id="spanish"),
    ])


def show(rec, now, energy):
    print(f"  {now:%a %H:%M}  energy {energy}/5 -> {rec.task.name}, {rec.minutes} min")
    print(f"      why: {'; '.join(rec.reasons)}")


def start(state, rec, energy, now):
    engine.record(state, rec.task, "accept", energy, now)
    rec.task.hours_left = round(max(0.0, rec.task.hours_left - rec.minutes / 60), 2)
    print(f"      user: Start ({rec.task.hours_left:g} h left on it)")


def scenario_evenings():
    """A student with medium energy in the evenings skips hard tasks."""
    print("Scenario A: evenings, user skips the hard task when it is suggested")
    state = make_state()
    for day in range(4):
        now = START + timedelta(days=day, hours=12)  # 21:00
        rec = engine.recommend(state, 3, now)
        show(rec, now, 3)
        if rec.task.id == "stats" and day < 3:
            engine.record(state, rec.task, "skip", 3, now)
            print("      user: Not now")
            rec = engine.recommend(state, 3, now, exclude={"stats"})
            if rec is None:
                print("      no other open tasks")
                continue
            show(rec, now, 3)
        start(state, rec, 3, now)
    print(f"  learned preferences: { {k: round(v, 2) for k, v in state.prefs.items()} }\n")
    return state


def scenario_morning():
    """Same tasks, morning, high energy: the hard task comes first."""
    print("Scenario B: Monday morning, high energy")
    state = make_state()
    rec = engine.recommend(state, 5, START)
    show(rec, START, 5)
    print()


def scenario_reset(state):
    """After an unusual week, the user resets learning and checks the export."""
    print("Scenario C: after an ill week, user resets learning, then exports")
    now = START + timedelta(days=4, hours=1)  # Friday 10:00
    print(f"  status before: {engine.learning_status(state)}")
    print(f"  learned: {engine.describe_prefs(state.prefs)}")
    engine.reset_learning(state)
    print("  user: Reset learning history -> Delete")
    print(f"  status after: {engine.learning_status(state)}")
    state.learning_enabled = False
    print("  user: switches 'Learn from my choices' off")
    rec = engine.recommend(state, 2, now)
    show(rec, now, 2)
    engine.record(state, rec.task, "skip", 2, now)
    print(f"  user: Not now -> records kept: {len(state.events)}")
    print("  export:")
    print("   ", json.dumps(engine.export(state, now), indent=2).replace("\n", "\n    "))


if __name__ == "__main__":
    scenario_morning()
    scenario_reset(scenario_evenings())
