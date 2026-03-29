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

    def __post_init__(self):
        """Validate that priority is between 1 and 5."""
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Priority must be between 1 and 5, got {self.priority}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary."""
        return {
            "name": self.name,
            "category": self.category.value,
            "duration": self.duration,
            "priority": self.priority,
            "time_of_day": self.time_of_day.value if self.time_of_day else None,
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


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet

    def rank_tasks(self) -> List[Task]:
        """Return the pet's tasks sorted by priority, highest first."""
        return sorted(self.pet.get_tasks(), key=lambda t: t.priority, reverse=True)

    def generate_plan(self) -> dict:
        """Build a daily plan by fitting ranked tasks within the owner's available time."""
        ranked = self.rank_tasks()
        available = self.owner.available_time
        scheduled = []
        skipped = []
        time_used = 0

        for task in ranked:
            if time_used + task.duration <= available:
                scheduled.append(task)
                time_used += task.duration
            else:
                skipped.append(task)

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
