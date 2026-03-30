# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan
888stem first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The scheduler goes beyond a simple to-do list with several logic improvements:

**Recurring tasks** — each `Task` has a `frequency` (`daily`, `weekly`, or `as_needed`). The scheduler calls `is_due()` before including a task in the plan, so weekly tasks are automatically suppressed until 7 days have passed. When a task is marked complete via `Pet.complete_task()`, a fresh copy is auto-generated for the next occurrence.

**Time-of-day ordering** — tasks have an optional `time_of_day` field (`morning`, `afternoon`, `evening`). The generated plan is always sorted into chronological order, regardless of the order tasks were added.

**Task filtering** — `Pet` supports filtering tasks by completion status (`get_tasks_by_status`) or category (`get_tasks_by_category`). `Owner` supports cross-pet filtering by pet name and/or completion status (`filter_tasks`).

**Conflict detection** — three levels of overlap checking, all returning warning strings (never crashing):
- `Scheduler.detect_time_overlaps()` — any two tasks for one pet sharing the same period
- `Scheduler.detect_conflicts()` — tasks whose combined duration exceeds the period's time budget
- `Owner.detect_cross_pet_overlaps()` — tasks across different pets competing for the same period

Call `owner.get_warnings()` or `scheduler.get_warnings()` for a single aggregated list of all warnings.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
