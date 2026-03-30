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


# --- next_occurrence / complete_task ---

def test_mark_complete_records_date(basic_task):
    basic_task.mark_complete("2026-03-29")
    assert basic_task.last_completed_date == "2026-03-29"

def test_next_occurrence_daily_returns_fresh_copy(basic_task):
    basic_task.mark_complete("2026-03-29")
    nxt = basic_task.next_occurrence()
    assert nxt is not basic_task
    assert nxt.completed is False
    assert nxt.name == basic_task.name

def test_next_occurrence_preserves_last_completed_date(basic_task):
    basic_task.mark_complete("2026-03-29")
    nxt = basic_task.next_occurrence()
    # next copy carries the date so is_due() works correctly for weekly tasks
    assert nxt.last_completed_date == "2026-03-29"

def test_next_occurrence_as_needed_returns_none():
    task = Task("Groom", Category.WALK, duration=15, priority=2, frequency="as_needed")
    task.mark_complete("2026-03-29")
    assert task.next_occurrence() is None

def test_complete_task_adds_next_occurrence(basic_pet, basic_task):
    basic_pet.add_task(basic_task)
    assert len(basic_pet.get_tasks()) == 1
    basic_pet.complete_task("Morning Walk", today="2026-03-29")
    assert len(basic_pet.get_tasks()) == 2
    original, next_task = basic_pet.get_tasks()
    assert original.completed is True
    assert next_task.completed is False

def test_complete_task_as_needed_does_not_add_copy(basic_pet):
    task = Task("Groom", Category.WALK, duration=15, priority=2, frequency="as_needed")
    basic_pet.add_task(task)
    basic_pet.complete_task("Groom", today="2026-03-29")
    assert len(basic_pet.get_tasks()) == 1  # no new copy added

def test_complete_task_raises_for_missing_task(basic_pet):
    with pytest.raises(ValueError):
        basic_pet.complete_task("Nonexistent")

def test_complete_task_weekly_next_occurrence_not_due_yet(basic_pet):
    task = Task("Bath", Category.WALK, duration=20, priority=3, frequency="weekly")
    basic_pet.add_task(task)
    basic_pet.complete_task("Bath", today="2026-03-29")
    owner = Owner("Alex", available_time=60)
    owner.add_pet(basic_pet)
    scheduler = Scheduler(owner, basic_pet)
    # next occurrence was just completed today — should not be due until 7 days later
    plan = scheduler.generate_plan(today="2026-03-30")
    scheduled_names = [t.name for t in plan["scheduled"]]
    assert scheduled_names.count("Bath") == 0  # completed copy excluded; next not due yet


# --- Feature 2: Pet filter methods ---

def test_get_tasks_by_status_completed(loaded_pet):
    loaded_pet.get_tasks()[0].mark_complete()
    completed = loaded_pet.get_tasks_by_status(True)
    assert len(completed) == 1
    assert completed[0].completed is True

def test_get_tasks_by_status_incomplete(loaded_pet):
    incomplete = loaded_pet.get_tasks_by_status(False)
    assert all(not t.completed for t in incomplete)
    assert len(incomplete) == len(loaded_pet.get_tasks())

def test_get_tasks_by_category_walk(loaded_pet):
    walks = loaded_pet.get_tasks_by_category(Category.WALK)
    assert all(t.category == Category.WALK for t in walks)
    assert len(walks) == 1

def test_get_tasks_by_category_appointment(loaded_pet):
    appointments = loaded_pet.get_tasks_by_category(Category.APPOINTMENT)
    assert len(appointments) == 1
    assert appointments[0].name == "Vet Appointment"

def test_get_tasks_by_category_no_match(basic_pet):
    result = basic_pet.get_tasks_by_category(Category.WALK)
    assert result == []


# --- Feature 3: Recurring tasks / is_due() ---

def test_is_due_daily_always_true():
    task = Task("Feed", Category.FEEDING, duration=10, priority=3, frequency="daily")
    assert task.is_due("2026-03-29") is True

def test_is_due_as_needed_always_true():
    task = Task("Groom", Category.WALK, duration=15, priority=2, frequency="as_needed")
    assert task.is_due("2026-03-29") is True

def test_is_due_weekly_never_done():
    task = Task("Flea Treatment", Category.MEDICATION, duration=5, priority=4, frequency="weekly")
    assert task.is_due("2026-03-29") is True

def test_is_due_weekly_recently_done():
    task = Task("Flea Treatment", Category.MEDICATION, duration=5, priority=4,
                frequency="weekly", last_completed_date="2026-03-26")
    assert task.is_due("2026-03-29") is False  # only 3 days ago

def test_is_due_weekly_exactly_seven_days():
    task = Task("Flea Treatment", Category.MEDICATION, duration=5, priority=4,
                frequency="weekly", last_completed_date="2026-03-22")
    assert task.is_due("2026-03-29") is True  # exactly 7 days

def test_frequency_validation():
    with pytest.raises(ValueError):
        Task("Bad", Category.WALK, duration=10, priority=3, frequency="monthly")

def test_generate_plan_excludes_not_due_tasks(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    task = Task("Bath", Category.WALK, duration=20, priority=5,
                frequency="weekly", last_completed_date="2026-03-28")
    basic_pet.add_task(task)
    scheduler = Scheduler(owner, basic_pet)
    plan = scheduler.generate_plan(today="2026-03-29")
    assert "Bath" not in [t.name for t in plan["scheduled"]]
    assert "Bath" not in [t.name for t in plan["skipped"]]


# --- Feature 1: Time-of-day ordering ---

def test_generate_plan_orders_by_time_of_day(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet  # 60 min available; all tasks fit
    basic_pet.add_task(Task("Evening Med", Category.MEDICATION, duration=5, priority=3,
                            time_of_day=TimeOfDay.EVENING))
    basic_pet.add_task(Task("Afternoon Walk", Category.WALK, duration=10, priority=3,
                            time_of_day=TimeOfDay.AFTERNOON))
    basic_pet.add_task(Task("Morning Feed", Category.FEEDING, duration=10, priority=3,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    scheduled = scheduler.generate_plan()["scheduled"]
    tod_values = [t.time_of_day for t in scheduled]
    assert tod_values.index(TimeOfDay.MORNING) < tod_values.index(TimeOfDay.AFTERNOON)
    assert tod_values.index(TimeOfDay.AFTERNOON) < tod_values.index(TimeOfDay.EVENING)

def test_generate_plan_none_time_of_day_sorted_last(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Untimed Task", Category.FEEDING, duration=5, priority=3))
    basic_pet.add_task(Task("Morning Feed", Category.FEEDING, duration=5, priority=3,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    scheduled = scheduler.generate_plan()["scheduled"]
    names = [t.name for t in scheduled]
    assert names.index("Morning Feed") < names.index("Untimed Task")


# --- Time overlap detection ---

def test_detect_time_overlaps_same_period(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=3,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    overlaps = scheduler.detect_time_overlaps()
    assert len(overlaps) == 1
    assert "morning" in overlaps[0].lower()
    assert "Buddy" in overlaps[0]

def test_detect_time_overlaps_different_periods(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=3,
                            time_of_day=TimeOfDay.EVENING))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.detect_time_overlaps() == []

def test_detect_time_overlaps_no_time_of_day(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=3))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.detect_time_overlaps() == []

def test_detect_cross_pet_overlaps(basic_pet):
    owner = Owner("Alex", available_time=90)
    luna = Pet(name="Luna", species="cat", breed="Siamese", age=2)
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    luna.add_task(Task("Feeding", Category.FEEDING, duration=10, priority=3,
                       time_of_day=TimeOfDay.MORNING))
    owner.add_pet(basic_pet)
    owner.add_pet(luna)
    overlaps = owner.detect_cross_pet_overlaps()
    assert len(overlaps) == 1
    assert "morning" in overlaps[0].lower()
    assert "Buddy" in overlaps[0]
    assert "Luna" in overlaps[0]

def test_detect_cross_pet_overlaps_no_conflict(basic_pet):
    owner = Owner("Alex", available_time=90)
    luna = Pet(name="Luna", species="cat", breed="Siamese", age=2)
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    luna.add_task(Task("Feeding", Category.FEEDING, duration=10, priority=3,
                       time_of_day=TimeOfDay.EVENING))
    owner.add_pet(basic_pet)
    owner.add_pet(luna)
    assert owner.detect_cross_pet_overlaps() == []

def test_detect_cross_pet_overlaps_single_pet(basic_pet):
    owner = Owner("Alex", available_time=60)
    basic_pet.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    owner.add_pet(basic_pet)
    # Only one pet — no cross-pet overlap possible
    assert owner.detect_cross_pet_overlaps() == []


# --- get_warnings() aggregator ---

def test_scheduler_get_warnings_returns_list(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, basic_pet)
    assert isinstance(scheduler.get_warnings(), list)

def test_scheduler_get_warnings_empty_when_no_issues(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Walk", Category.WALK, duration=10, priority=3,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.get_warnings() == []

def test_scheduler_get_warnings_aggregates_overlap_and_conflict(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet  # 60 min; morning budget = 20 min
    basic_pet.add_task(Task("Walk", Category.WALK, duration=15, priority=5,
                            time_of_day=TimeOfDay.MORNING))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=4,
                            time_of_day=TimeOfDay.MORNING))  # overlap + budget conflict
    scheduler = Scheduler(owner, basic_pet)
    warnings = scheduler.get_warnings()
    assert len(warnings) == 2  # one from detect_time_overlaps, one from detect_conflicts
    assert all(isinstance(w, str) for w in warnings)

def test_owner_get_warnings_returns_list(owner_with_pet):
    owner, _ = owner_with_pet
    assert isinstance(owner.get_warnings(), list)

def test_owner_get_warnings_includes_cross_pet_overlap():
    owner = Owner("Alex", available_time=90)
    buddy = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    luna = Pet(name="Luna", species="cat", breed="Siamese", age=2)
    buddy.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                        time_of_day=TimeOfDay.MORNING))
    luna.add_task(Task("Feed", Category.FEEDING, duration=10, priority=3,
                       time_of_day=TimeOfDay.MORNING))
    owner.add_pet(buddy)
    owner.add_pet(luna)
    warnings = owner.get_warnings()
    assert any("Cross-pet" in w for w in warnings)

def test_owner_get_warnings_no_issues_returns_empty():
    owner = Owner("Alex", available_time=90)
    buddy = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
    buddy.add_task(Task("Walk", Category.WALK, duration=20, priority=4,
                        time_of_day=TimeOfDay.MORNING))
    owner.add_pet(buddy)
    assert owner.get_warnings() == []


# --- Feature 4: Conflict detection ---

def test_detect_conflicts_none_when_single_task_per_period(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Walk", Category.WALK, duration=15, priority=4,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.detect_conflicts() == []

def test_detect_conflicts_flags_overloaded_period(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet  # 60 min; morning budget = 20 min
    basic_pet.add_task(Task("Walk", Category.WALK, duration=15, priority=5,
                            time_of_day=TimeOfDay.MORNING))
    basic_pet.add_task(Task("Feed", Category.FEEDING, duration=10, priority=4,
                            time_of_day=TimeOfDay.MORNING))  # 15 + 10 = 25 > 20
    scheduler = Scheduler(owner, basic_pet)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "morning" in conflicts[0].lower()

def test_detect_conflicts_single_large_task_not_a_conflict(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Long Walk", Category.WALK, duration=60, priority=5,
                            time_of_day=TimeOfDay.MORNING))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.detect_conflicts() == []

def test_detect_conflicts_none_time_of_day_ignored(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    basic_pet.add_task(Task("Untimed A", Category.FEEDING, duration=40, priority=3))
    basic_pet.add_task(Task("Untimed B", Category.FEEDING, duration=40, priority=3))
    scheduler = Scheduler(owner, basic_pet)
    assert scheduler.detect_conflicts() == []

def test_detect_conflicts_returns_list(basic_pet, owner_with_pet):
    owner, _ = owner_with_pet
    scheduler = Scheduler(owner, basic_pet)
    assert isinstance(scheduler.detect_conflicts(), list)
