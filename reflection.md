# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
- Answer: We should be able to enter owner + pet information, add and edit tasks, and generate a daily plan with reasoning. The four classes we included are Pet, Task, Scheduler, and Owner. Pet is a single care item that holds the data describing what needs to be done. The Pet class is the animal being cared for. Owner is the pets owner. And scheduler takes an owner and a pet, and fits them in with the owner's available time and produces a daily plan. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
- Answer: There were a few missing relationships like scheduler having no link to owner.available_time and no way to remove or edit a task from pet. The changes we made were adding a remove_task method, changing category and time of day to an Enum to prevent invalid values, add priority validation, and have scheduler pull tasks fresh in generate_plan method instead of caching at init. 
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- Answer: The scheduler considers two hard constraints and two soft constraints. Hard constraints are available time (tasks are dropped to skipped if they don't fit within owner.available_time) and due date (weekly tasks are excluded if completed within the last 7 days). Soft constraints are priority (rank_tasks() sorts highest priority first so high-priority tasks claim time before lower ones) and time of day (the final scheduled list is sorted morning → afternoon → evening → unassigned). The hard constraints determine what gets scheduled at all; the soft constraints determine order and presentation.
- How did you decide which constraints mattered most?
- Answer: Available time and due date matter most because violating them produces incorrect behavior — scheduling more than the owner has time for, or showing a task that shouldn't appear yet. Priority and time-of-day are ordering preferences that improve the plan's quality but don't break it if wrong. We prioritized correctness over polish.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
- Answer: The scheduler uses a greedy algorithm — it picks tasks in priority order and fits each one in until time runs out, without looking ahead. This can produce a suboptimal schedule: a single high-priority long task might consume most of the time budget and cause several shorter high-value tasks to be skipped, whereas a smarter knapsack-style solver could fit more total value into the same window. The tradeoff is reasonable here because pet care tasks are simple enough that priority order closely reflects what the owner actually wants done first — medications and feedings rank high and are short, so they almost always fit. The tasks most likely to be skipped (vet appointments, long grooming sessions) are genuinely the ones an owner would deprioritize on a busy day. The greedy approach also stays fast, transparent, and easy to explain in the UI.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- Answer: AI was used at every stage of the project. During design we brainstormed the four core classes, identified missing relationships (like Scheduler having no link to owner.available_time), and drafted the UML diagram. During implementation AI generated class skeletons with dataclass decorators, implemented method bodies, and suggested improvements like switching category and time_of_day to Enums and adding priority validation in __post_init__. During testing AI identified edge cases we hadn't considered — like calling complete_task() twice, tasks at the exact time budget boundary, and weekly tasks with a future last_completed_date. For refactoring it consolidated conflict detection into the get_warnings() aggregator pattern and added docstrings to all algorithmic methods.
- What kinds of prompts or questions were most helpful?
- Answer: The most useful prompts were specific and structural: "what are the missing relationships or potential logic bottlenecks in this file?" and "what are the most important edge cases to test for a scheduler with sorting and recurring tasks?" Open-ended design questions like "brainstorm the main objects needed" were good for getting started, but targeted questions about specific behaviors or gaps produced the most actionable output.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
- Answer: When AI suggested caching tasks in Scheduler.__init__ as self.tasks = pet.get_tasks(), we identified this as a bug — if tasks changed on the pet after the scheduler was created, the scheduler would use stale data. We changed generate_plan() to pull tasks fresh from the pet each time it runs instead. We verified this by reasoning through what would happen if Pet.add_task() was called after Scheduler was instantiated: with caching, the new task would be invisible to the scheduler; without it, every generate_plan() call sees the current state. The test suite confirmed the correct behavior.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Answer: We tested five core areas: (1) greedy scheduling stays within available time and correctly populates scheduled vs skipped; (2) `is_due()` correctly gates weekly tasks including the exact 7-day boundary; (3) `complete_task()` marks tasks done, auto-generates the next occurrence, and only matches incomplete tasks so calling it twice completes each copy in turn; (4) sort order places tasks in MORNING → AFTERNOON → EVENING → unassigned order and is stable within the same period; (5) conflict detection returns warning strings at the per-pet and cross-pet level without crashing.
- Why were these tests important?
- Answer: These tests matter because the scheduler's output is only trustworthy if the constraints are enforced correctly. A bug in `is_due()` could silently drop or duplicate tasks. A bug in `complete_task()` — which we actually caught during testing — was re-completing already-done tasks instead of the next copy, which would have caused incorrect task counts and confusing schedules. Tests gave us confidence to refactor freely without introducing regressions.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- Answer: High confidence for the core scheduling loop, task filtering, and recurring task logic — all are well-covered. Moderate confidence around edge cases involving multiple pets sharing time budgets, since each pet currently gets the full available time independently. The warning system catches overlaps but the plan itself doesn't enforce a shared budget.
- What edge cases would you test next if you had more time?
- Answer: (1) Zero available time — verified, nothing schedules. (2) Task duration exactly equals available time — verified, it schedules correctly. (3) A `last_completed_date` set in the future — verified, correctly treated as not due. (4) The behavior when both a completed original and its copy are daily — both appear in the plan, which is technically correct but could surprise a user. (5) Shared time budget across multiple pets — currently untested and the most realistic gap for a real-world scenario.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

- Answers: I like the planning, brainstorming, and building tests. Using AI to build UI is kind of bad, though. I would improve the way adding a tasks works with the UI because it's a little bit janky and not nice to look at. Using Enums was something I found interesting for Category and TimeOfDay. Also, the streamlit states are nice features. 