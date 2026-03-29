from pawpal_system import Task, Pet, Owner, Scheduler, Category, TimeOfDay

# --- Owner ---
owner = Owner(name="Alex", available_time=90)

# --- Pet 1: Buddy the dog ---
buddy = Pet(name="Buddy", species="dog", breed="Labrador", age=3)
buddy.add_task(Task("Morning Walk", Category.WALK, duration=30, priority=5, time_of_day=TimeOfDay.MORNING))
buddy.add_task(Task("Breakfast", Category.FEEDING, duration=10, priority=4, time_of_day=TimeOfDay.MORNING))
buddy.add_task(Task("Heartworm Pill", Category.MEDICATION, duration=5, priority=5, time_of_day=TimeOfDay.MORNING))
buddy.add_task(Task("Evening Walk", Category.WALK, duration=30, priority=3, time_of_day=TimeOfDay.EVENING))

# --- Pet 2: Luna the cat ---
luna = Pet(name="Luna", species="cat", breed="Siamese", age=2)
luna.add_task(Task("Breakfast", Category.FEEDING, duration=5, priority=4, time_of_day=TimeOfDay.MORNING))
luna.add_task(Task("Flea Treatment", Category.MEDICATION, duration=5, priority=5, time_of_day=TimeOfDay.AFTERNOON))
luna.add_task(Task("Vet Checkup", Category.APPOINTMENT, duration=60, priority=3, time_of_day=TimeOfDay.AFTERNOON))

owner.add_pet(buddy)
owner.add_pet(luna)

# --- Print today's schedule for each pet ---
print("=" * 50)
print(f"TODAY'S SCHEDULE FOR {owner.name.upper()}")
print(f"Total time available: {owner.available_time} min")
print("=" * 50)

for pet in owner.get_pets():
    scheduler = Scheduler(owner, pet)
    print(f"\n{scheduler.explain_plan()}")
    print("-" * 50)
