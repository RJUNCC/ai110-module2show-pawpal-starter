import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Category, TimeOfDay


# --- Fixtures ---

@pytest.fixture
def basic_task():
    return Task("Morning Walk", Category.WALK, duration=30, priority=5, time_of_day=TimeOfDay.MORNING)

@pytest.fixture
def basic_pet():
    return Pet(name="Buddy", species="dog", breed="Labrador", age=3)

@pytest.fixture
def owner_with_pet(basic_pet):
    owner = Owner(name="Alex", available_time=60)
    owner.add_pet(basic_pet)
    return owner, basic_pet

@pytest.fixture
def loaded_pet(basic_pet):
    basic_pet.add_task(Task("Morning Walk", Category.WALK, duration=30, priority=5, time_of_day=TimeOfDay.MORNING))
    basic_pet.add_task(Task("Breakfast", Category.FEEDING, duration=10, priority=4))
    basic_pet.add_task(Task("Heartworm Pill", Category.MEDICATION, duration=5, priority=5))
    basic_pet.add_task(Task("Vet Appointment", Category.APPOINTMENT, duration=60, priority=3))
    return basic_pet


# --- Task tests ---

def test_task_to_dict(basic_task):
    d = basic_task.to_dict()
    assert d["name"] == "Morning Walk"
    assert d["category"] == "walk"
    assert d["duration"] == 30
    assert d["priority"] == 5
    assert d["time_of_day"] == "morning"

def test_task_to_dict_no_time_of_day():
    task = Task("Pill", Category.MEDICATION, duration=5, priority=5)
    assert task.to_dict()["time_of_day"] is None

def test_task_priority_validation_low():
    with pytest.raises(ValueError):
        Task("Bad", Category.WALK, duration=10, priority=0)

def test_task_priority_validation_high():
    with pytest.raises(ValueError):
        Task("Bad", Category.WALK, duration=10, priority=99)

def test_task_priority_boundary_valid():
    t1 = Task("Low", Category.WALK, duration=10, priority=1)
    t2 = Task("High", Category.WALK, duration=10, priority=5)
    assert t1.priority == 1
    assert t2.priority == 5

def test_mark_complete_changes_status(basic_task):
    assert basic_task.completed is False
    basic_task.mark_complete()
    assert basic_task.completed is True

def test_mark_complete_is_idempotent(basic_task):
    basic_task.mark_complete()
    basic_task.mark_complete()
    assert basic_task.completed is True


# --- Pet tests ---

def test_add_task_increases_count(basic_pet, basic_task):
    assert len(basic_pet.get_tasks()) == 0
    basic_pet.add_task(basic_task)
    assert len(basic_pet.get_tasks()) == 1

def test_add_multiple_tasks(basic_pet):
    basic_pet.add_task(Task("Walk", Category.WALK, duration=30, priority=5))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=4))
    assert len(basic_pet.get_tasks()) == 2

def test_remove_task(basic_pet, basic_task):
    basic_pet.add_task(basic_task)
    basic_pet.remove_task("Morning Walk")
    assert len(basic_pet.get_tasks()) == 0

def test_remove_nonexistent_task_does_not_raise(basic_pet):
    basic_pet.remove_task("Nonexistent")  # should not raise

def test_edit_task(basic_pet, basic_task):
    basic_pet.add_task(basic_task)
    basic_pet.edit_task("Morning Walk", duration=20, priority=3)
    task = basic_pet.get_tasks()[0]
    assert task.duration == 20
    assert task.priority == 3

def test_edit_nonexistent_task_raises(basic_pet):
    with pytest.raises(ValueError):
        basic_pet.edit_task("Ghost Task", duration=10)


# --- Owner tests ---

def test_add_pet(basic_pet):
    owner = Owner("Alex", available_time=60)
    owner.add_pet(basic_pet)
    assert len(owner.get_pets()) == 1

def test_owner_get_pets_empty():
    owner = Owner("Alex", available_time=60)
    assert owner.get_pets() == []


# --- Scheduler tests ---

def test_rank_tasks_by_priority(loaded_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, loaded_pet)
    ranked = scheduler.rank_tasks()
    priorities = [t.priority for t in ranked]
    assert priorities == sorted(priorities, reverse=True)

def test_generate_plan_respects_available_time(loaded_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, loaded_pet)
    plan = scheduler.generate_plan()
    assert plan["time_used"] <= owner.available_time

def test_generate_plan_skips_tasks_that_dont_fit(loaded_pet, owner_with_pet):
    owner, _ = owner_with_pet  # 60 min available; Vet Appointment is 60 min but lower priority
    scheduler = Scheduler(owner, loaded_pet)
    plan = scheduler.generate_plan()
    skipped_names = [t.name for t in plan["skipped"]]
    assert "Vet Appointment" in skipped_names

def test_generate_plan_empty_tasks(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, basic_pet)
    plan = scheduler.generate_plan()
    assert plan["scheduled"] == []
    assert plan["time_used"] == 0

def test_explain_plan_contains_pet_name(loaded_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, loaded_pet)
    explanation = scheduler.explain_plan()
    assert "Buddy" in explanation

def test_explain_plan_mentions_skipped(loaded_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, loaded_pet)
    explanation = scheduler.explain_plan()
    assert "Skipped" in explanation
