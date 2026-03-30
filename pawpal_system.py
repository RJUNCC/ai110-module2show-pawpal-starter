import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Category(Enum):
    FEEDING = "feeding"
    WALK = "walk"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"


class TimeOfDay(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


@dataclass
class Task:
    name: str
    category: Category
    duration: int  # minutes
    priority: int  # 1 (low) to 5 (high)
    time_of_day: Optional[TimeOfDay] = None
    completed: bool = False
    frequency: str = "daily"            # "daily" | "weekly" | "as_needed"
    last_completed_date: Optional[str] = None  # ISO date e.g. "2026-03-22"

    def __post_init__(self):
        """Validate priority (1-5) and frequency value."""
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Priority must be between 1 and 5, got {self.priority}")
        if self.frequency not in ("daily", "weekly", "as_needed"):
            raise ValueError(f"frequency must be 'daily', 'weekly', or 'as_needed', got {self.frequency!r}")

    def mark_complete(self, today: str = None) -> None:
        """Mark this task as completed and record the completion date."""
        self.completed = True
        self.last_completed_date = today or datetime.date.today().isoformat()

    def next_occurrence(self) -> Optional["Task"]:
        """Return a fresh copy of this task for its next occurrence, or None for as_needed tasks.

        The copy preserves last_completed_date so is_due() can correctly gate
        weekly tasks until 7 days have elapsed. completed is reset to False.
        """
        if self.frequency == "as_needed":
            return None
        from dataclasses import replace
        return replace(self, completed=False)

    def is_due(self, today: str) -> bool:
        """Return True if this task should appear in today's schedule.

        - daily: always due
        - as_needed: always due (owner decides when to act on it)
        - weekly: due if never completed, or if 7+ days have passed since last_completed_date
        """
        if self.frequency in ("daily", "as_needed"):
            return True
        if self.last_completed_date is None:
            return True
        last = datetime.date.fromisoformat(self.last_completed_date)
        current = datetime.date.fromisoformat(today)
        return (current - last).days >= 7

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary."""
        return {
            "name": self.name,
            "category": self.category.value,
            "duration": self.duration,
            "priority": self.priority,
            "time_of_day": self.time_of_day.value if self.time_of_day else None,
            "frequency": self.frequency,
            "last_completed_date": self.last_completed_date,
        }


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    health_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks associated with this pet."""
        return self.tasks

    def get_tasks_by_status(self, completed: bool) -> List[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self.tasks if t.completed == completed]

    def get_tasks_by_category(self, category: Category) -> List[Task]:
        """Return tasks filtered by category."""
        return [t for t in self.tasks if t.category == category]

    def complete_task(self, task_name: str, today: str = None) -> None:
        """Mark a task complete and auto-add the next occurrence for daily/weekly tasks.

        Only matches incomplete tasks — skips already-completed ones so calling
        this twice completes each copy in turn rather than re-completing the original.
        """
        for task in self.tasks:
            if task.name == task_name and not task.completed:
                task.mark_complete(today)
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.tasks.append(next_task)
                return
        raise ValueError(f"Task '{task_name}' not found or already completed")

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name, silently ignoring if not found."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def edit_task(self, task_name: str, **kwargs) -> None:
        """Update fields on an existing task by name, raising ValueError if not found."""
        for task in self.tasks:
            if task.name == task_name:
                for key, value in kwargs.items():
                    setattr(task, key, value)
                return
        raise ValueError(f"Task '{task_name}' not found")


class Owner:
    def __init__(self, name: str, available_time: int):
        self.name = name
        self.available_time = available_time  # minutes per day
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner."""
        return self.pets

    def detect_cross_pet_overlaps(self) -> List[str]:
        """Return warnings when tasks across different pets share the same time-of-day period."""
        # Map each period to a list of (pet_name, task) tuples
        buckets: dict = defaultdict(list)
        for pet in self.pets:
            for task in pet.get_tasks():
                if task.time_of_day is not None:
                    buckets[task.time_of_day].append((pet.name, task))
        warnings = []
        for period, entries in buckets.items():
            pet_names = [pet_name for pet_name, _ in entries]
            if len(set(pet_names)) > 1:
                detail = ", ".join(f"{pn}: {t.name}" for pn, t in entries)
                warnings.append(
                    f"Cross-pet overlap in {period.value}: [{detail}]"
                )
        return warnings

    def get_warnings(self) -> List[str]:
        """Return all conflict and overlap warnings across all pets as a flat list of strings."""
        warnings = []
        try:
            for pet in self.pets:
                scheduler = Scheduler(self, pet)
                warnings.extend(scheduler.get_warnings())
            warnings.extend(self.detect_cross_pet_overlaps())
        except Exception as e:
            warnings.append(f"Warning: conflict check failed: {e}")
        return warnings

    def filter_tasks(self, pet_name: str = None, completed: bool = None) -> List[Task]:
        """Return tasks across all pets, optionally filtered by pet name and/or completion status."""
        results = []
        for pet in self.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results


_TIME_ORDER = {TimeOfDay.MORNING: 0, TimeOfDay.AFTERNOON: 1, TimeOfDay.EVENING: 2}


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet

    def rank_tasks(self) -> List[Task]:
        """Return the pet's tasks sorted by priority, highest first."""
        return sorted(self.pet.get_tasks(), key=lambda t: t.priority, reverse=True)

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by time of day (morning → afternoon → evening → unassigned)."""
        return sorted(tasks, key=lambda t: _TIME_ORDER.get(t.time_of_day, 3))

    def generate_plan(self, today: str = None) -> dict:
        """Build a daily plan fitting due, ranked tasks within available time, ordered by time of day.

        Uses a greedy algorithm: tasks are sorted by priority (highest first), then
        each task is scheduled if it fits within the remaining available time.
        Tasks excluded by is_due() are silently omitted (not listed in skipped).
        The final scheduled list is sorted by time_of_day: morning → afternoon → evening → unassigned.
        """
        if today is None:
            today = datetime.date.today().isoformat()
        ranked = [t for t in self.rank_tasks() if t.is_due(today)]
        available = self.owner.available_time
        scheduled, skipped, time_used = [], [], 0

        for task in ranked:
            if time_used + task.duration <= available:
                scheduled.append(task)
                time_used += task.duration
            else:
                skipped.append(task)

        scheduled = self.sort_by_time(scheduled)

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "time_used": time_used,
            "time_available": available,
        }

    def explain_plan(self) -> str:
        """Return a human-readable summary of the daily plan including skipped tasks."""
        plan = self.generate_plan()
        lines = [f"Daily plan for {self.pet.name} ({self.owner.available_time} min available):\n"]

        lines.append("Scheduled tasks:")
        for task in plan["scheduled"]:
            lines.append(f"  - {task.name} ({task.category.value}, {task.duration} min, priority {task.priority})")

        if plan["skipped"]:
            lines.append("\nSkipped tasks (not enough time):")
            for task in plan["skipped"]:
                lines.append(f"  - {task.name} ({task.duration} min, priority {task.priority})")

        lines.append(f"\nTime used: {plan['time_used']} / {plan['time_available']} min")
        return "\n".join(lines)

    def detect_time_overlaps(self) -> List[str]:
        """Return warnings for any two tasks on this pet sharing the same time-of-day period."""
        warnings = []
        buckets: dict = defaultdict(list)
        for task in self.pet.get_tasks():
            if task.time_of_day is not None:
                buckets[task.time_of_day].append(task)
        for period, tasks in buckets.items():
            if len(tasks) > 1:
                names = ", ".join(t.name for t in tasks)
                warnings.append(
                    f"{self.pet.name} has overlapping tasks in {period.value}: [{names}]"
                )
        return warnings

    def detect_conflicts(self) -> List[str]:
        """Return human-readable warnings for time-of-day scheduling conflicts.

        A conflict is flagged when 2+ tasks share a time_of_day period and their
        combined duration exceeds 1/3 of the owner's available time (the assumed
        budget per period). A single oversized task is not flagged.
        """
        warnings = []
        period_budget = self.owner.available_time / 3
        buckets: dict = defaultdict(list)
        for task in self.pet.get_tasks():
            if task.time_of_day is not None:
                buckets[task.time_of_day].append(task)
        for period, tasks in buckets.items():
            if len(tasks) > 1:
                total = sum(t.duration for t in tasks)
                if total > period_budget:
                    names = ", ".join(t.name for t in tasks)
                    warnings.append(
                        f"Conflict in {period.value}: [{names}] total {total} min "
                        f"but only {period_budget:.0f} min available in this period."
                    )
        return warnings

    def get_warnings(self) -> List[str]:
        """Return all conflict and overlap warnings for this pet as a flat list of strings."""
        warnings = []
        try:
            warnings.extend(self.detect_time_overlaps())
            warnings.extend(self.detect_conflicts())
        except Exception as e:
            warnings.append(f"Warning: conflict check failed for {self.pet.name}: {e}")
        return warnings
