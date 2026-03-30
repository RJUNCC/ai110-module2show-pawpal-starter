from pawpal_system import Task, Pet, Owner, Scheduler, Category, TimeOfDay

# --- Owner ---
owner = Owner(name="Alex", available_time=90)

# --- Pet 1: Buddy (two morning tasks intentionally overlap) ---
buddy = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
buddy.add_task(Task("Evening Walk",    Category.WALK,       duration=30, priority=3, time_of_day=TimeOfDay.EVENING))
buddy.add_task(Task("Heartworm Pill",  Category.MEDICATION, duration=5,  priority=5, time_of_day=TimeOfDay.MORNING))
buddy.add_task(Task("Afternoon Play",  Category.WALK,       duration=20, priority=2, time_of_day=TimeOfDay.AFTERNOON))
buddy.add_task(Task("Breakfast",       Category.FEEDING,    duration=10, priority=4, time_of_day=TimeOfDay.MORNING))
buddy.add_task(Task("Morning Groom",   Category.WALK,       duration=20, priority=3, time_of_day=TimeOfDay.MORNING))

# --- Pet 2: Luna (tasks added out of order) ---
luna = Pet(name="Luna", species="cat", breed="Siamese", age=2)
luna.add_task(Task("Vet Checkup",    Category.APPOINTMENT, duration=60, priority=3, time_of_day=TimeOfDay.AFTERNOON))
luna.add_task(Task("Flea Treatment", Category.MEDICATION,  duration=5,  priority=5, time_of_day=TimeOfDay.AFTERNOON))
luna.add_task(Task("Breakfast",      Category.FEEDING,     duration=5,  priority=4, time_of_day=TimeOfDay.MORNING))

owner.add_pet(buddy)
owner.add_pet(luna)

# --- Mark a couple tasks complete for demo purposes ---
buddy.get_tasks()[1].mark_complete()   # Heartworm Pill
luna.get_tasks()[2].mark_complete()    # Breakfast

# =====================================================
print("=" * 55)
print(f"TODAY'S SCHEDULE FOR {owner.name.upper()}")
print("=" * 55)

# --- Sorted schedule per pet ---
for pet in owner.get_pets():
    scheduler = Scheduler(owner, pet)
    plan = scheduler.generate_plan()

    print(f"\n{pet.name}'s tasks (sorted by time of day):")
    for task in scheduler.sort_by_time(pet.get_tasks()):
        status = "✓" if task.completed else " "
        print(f"  [{status}] {task.time_of_day.value if task.time_of_day else 'anytime':12} "
              f"{task.name} ({task.duration} min, priority {task.priority})")

    for warning in scheduler.get_warnings():
        print(f"  ! WARNING: {warning}")

# --- Owner-level warnings (cross-pet overlaps) ---
print("\n" + "=" * 55)
print("ALL WARNINGS")
print("=" * 55)
all_warnings = owner.get_warnings()
if all_warnings:
    for w in all_warnings:
        print(f"  ! {w}")
else:
    print("  No warnings.")

# =====================================================
print("\n" + "=" * 55)
print("FILTER DEMOS")
print("=" * 55)

# Filter: all incomplete tasks across all pets
incomplete = owner.filter_tasks(completed=False)
print(f"\nAll incomplete tasks ({len(incomplete)}):")
for t in incomplete:
    print(f"  - {t.name}")

# Filter: all completed tasks across all pets
done = owner.filter_tasks(completed=True)
print(f"\nAll completed tasks ({len(done)}):")
for t in done:
    print(f"  - {t.name}")

# Filter: only Buddy's tasks
buddy_tasks = owner.filter_tasks(pet_name="Buddy")
print(f"\nBuddy's tasks only ({len(buddy_tasks)}):")
for t in buddy_tasks:
    print(f"  - {t.name}")

# Filter: Buddy's incomplete tasks
buddy_incomplete = owner.filter_tasks(pet_name="Buddy", completed=False)
print(f"\nBuddy's incomplete tasks ({len(buddy_incomplete)}):")
for t in buddy_incomplete:
    print(f"  - {t.name}")

# Filter by category: all walks across all pets
walk_tasks = [t for pet in owner.get_pets() for t in pet.get_tasks_by_category(Category.WALK)]
print(f"\nAll walk tasks across all pets ({len(walk_tasks)}):")
for t in walk_tasks:
    print(f"  - {t.name}")
