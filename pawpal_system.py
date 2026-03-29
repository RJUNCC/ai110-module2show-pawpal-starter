from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    name: str
    category: str  # "feeding" | "walk" | "medication" | "appointment"
    duration: int  # minutes
    priority: int  # 1 (low) to 5 (high)
    time_of_day: Optional[str] = None  # "morning" | "afternoon" | "evening"

    def to_dict(self) -> dict:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    health_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass


class Owner:
    def __init__(self, name: str, available_time: int):
        self.name = name
        self.available_time = available_time  # minutes per day
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_pets(self) -> List[Pet]:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: List[Task] = pet.get_tasks()

    def rank_tasks(self) -> List[Task]:
        pass

    def generate_plan(self) -> dict:
        pass

    def explain_plan(self) -> str:
        pass
