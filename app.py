"""FocusFlow Streamlit interface (v3).

Run with:  streamlit run app.py
"""
import json
from datetime import datetime, time

import streamlit as st

from focusflow import engine, storage

st.set_page_config(page_title="FocusFlow", page_icon="⏱")
st.title("FocusFlow")

if "state" not in st.session_state:
    st.session_state.state = storage.load()
    st.session_state.skipped = set()
state = st.session_state.state
now = datetime.now()
if engine.purge_old(state, now):  # privacy: drop choice records older than 14 days
    storage.save(state)

# ---- Settings: global controls (G17) and privacy ---------------------------
with st.sidebar:
    st.header("Settings")
    enabled = st.toggle(
        "Learn from my choices",
        value=state.learning_enabled,
        help="FocusFlow notices which tasks you skip or start at different times "
             "of day and adjusts future suggestions.",
    )
    if enabled != state.learning_enabled:
        state.learning_enabled = enabled
        storage.save(state)
        st.rerun()

    st.caption(engine.learning_status(state))
    learned = engine.describe_prefs(state.prefs)
    if learned:
        st.markdown("**What FocusFlow has learned**")
        for line in learned:
            st.markdown(f"- {line}")

    if st.button("Reset learning history"):
        st.session_state.confirm_reset = True
    if st.session_state.get("confirm_reset"):
        st.warning("This deletes what FocusFlow has learned about your study habits. "
                   "Your tasks and deadlines will not be affected.")
        c1, c2 = st.columns(2)
        if c1.button("Delete", type="primary"):
            engine.reset_learning(state)
            storage.save(state)
            st.session_state.confirm_reset = False
            st.rerun()
        if c2.button("Cancel"):
            st.session_state.confirm_reset = False
            st.rerun()

    st.divider()
    st.download_button(
        "Export my data",
        json.dumps(engine.export(state, now), indent=2),
        file_name="focusflow-export.json",
        mime="application/json",
    )
    st.caption(f"Choice records and energy ratings are deleted after {engine.RETENTION_DAYS} days. "
               "FocusFlow does not record mouse movement or typing.")

# ---- What the system can do (G1) -------------------------------------------
with st.expander("What FocusFlow does", expanded=not state.tasks):
    st.write(
        "FocusFlow suggests which task to study now and for how long, based on "
        "deadlines, work left, difficulty and how much energy you have. It can learn "
        "from the suggestions you skip or start; you can switch this off in Settings. "
        "It does not do your work for you, and it can be wrong, so you always choose."
    )

# ---- Add tasks --------------------------------------------------------------
with st.expander("Add a task", expanded=not state.tasks):
    with st.form("add_task", clear_on_submit=True):
        name = st.text_input("Task")
        deadline = st.date_input("Deadline")
        hours = st.number_input("Hours left", 0.5, 40.0, 2.0, 0.5)
        difficulty = st.slider("Difficulty", 1, 5, 3, help="1 = easy, 5 = hard")
        if st.form_submit_button("Add task") and name:
            state.tasks.append(engine.Task(name, datetime.combine(deadline, time(23, 59)), hours, difficulty))
            storage.save(state)
            st.rerun()

# ---- Recommendation ---------------------------------------------------------
energy = st.slider("How much energy do you have right now?", 1, 5, 3,
                   help="1 = exhausted, 5 = fully alert")
rec = engine.recommend(state, energy, now, exclude=st.session_state.skipped)

if rec is None:
    st.info("Add a task to get a suggestion." if not state.tasks else "No other open tasks.")
else:
    st.subheader(f"Do now: {rec.task.name}")
    st.caption("Why: " + "; ".join(rec.reasons) + ".")                     # G11
    if rec.runner_up:                                                       # G2
        st.caption(f"Close call: {rec.runner_up.name} is almost as good a choice.")
    if state.learning_enabled and len(state.events) < engine.SETTLED_AFTER:  # G2
        st.caption(engine.learning_status(state))
    minutes = st.slider("Minutes", 10, 90, rec.minutes, 5)                  # G9

    c1, c2 = st.columns(2)
    if c1.button("Start", type="primary"):
        engine.record(state, rec.task, "accept", energy, now)
        rec.task.hours_left = round(max(0.0, rec.task.hours_left - minutes / 60), 2)
        st.session_state.skipped = set()
        storage.save(state)
        st.success(f"Started {rec.task.name} for {minutes} minutes. {rec.task.hours_left:.1f} h left on it.")
    if c2.button("Not now"):
        engine.record(state, rec.task, "skip", energy, now)
        st.session_state.skipped.add(rec.task.id)
        storage.save(state)
        st.rerun()

    others = [t for t in state.tasks if t.hours_left > 0 and t.id != rec.task.id]
    if others:
        pick = st.selectbox("Or choose another task", ["—"] + [t.name for t in others])
        if pick != "—" and st.button("Start this instead"):
            chosen = next(t for t in others if t.name == pick)
            engine.record(state, chosen, "change", energy, now)
            chosen.hours_left = round(max(0.0, chosen.hours_left - minutes / 60), 2)
            storage.save(state)
            st.success(f"Started {chosen.name} for {minutes} minutes.")

# ---- Task list --------------------------------------------------------------
st.divider()
st.subheader("Your tasks")
for t in sorted(state.tasks, key=lambda t: t.deadline):
    c1, c2 = st.columns([5, 1])
    c1.write(f"**{t.name}** · due {t.deadline:%a %d %b} · {t.hours_left:.1f} h left · difficulty {t.difficulty}/5")
    if c2.button("Delete", key=f"del_{t.id}"):
        state.tasks.remove(t)
        storage.save(state)
        st.rerun()
