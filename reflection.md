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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
