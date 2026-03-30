import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Category, TimeOfDay

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Daily pet care scheduling assistant")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None

# =========================================================
# SECTION 1: Owner & Pet Setup
# =========================================================
st.header("1. Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Time available today (min)", min_value=10, max_value=480, value=60)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Mixed")
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

if st.button("Save Owner & Pet", type="primary"):
    owner = Owner(name=owner_name, available_time=int(available_time))
    pet = Pet(name=pet_name, species=species, breed=breed, age=int(age))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.success(f"Saved {owner_name} with {pet_name} ({species}, age {age}).")

if st.session_state.owner is None:
    st.info("Fill in owner and pet info above to get started.")
    st.stop()

owner = st.session_state.owner
pet = st.session_state.pet

st.divider()

# =========================================================
# SECTION 2: Add a Task
# =========================================================
st.header("2. Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Task name", value="Morning walk")
    category = st.selectbox("Category", [c.value for c in Category])
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority = st.selectbox("Priority (1=low, 5=high)", [1, 2, 3, 4, 5], index=4)
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
    time_of_day_raw = st.selectbox("Time of day", ["None"] + [t.value for t in TimeOfDay])

if st.button("Add Task", type="primary"):
    task = Task(
        name=task_name,
        category=Category(category),
        duration=int(duration),
        priority=priority,
        frequency=frequency,
        time_of_day=TimeOfDay(time_of_day_raw) if time_of_day_raw != "None" else None,
    )
    pet.add_task(task)
    st.success(f"Added: {task_name} ({category}, {duration} min, priority {priority})")

st.divider()

# =========================================================
# SECTION 3: Current Tasks with Filtering
# =========================================================
st.header("3. Current Tasks")

all_tasks = pet.get_tasks()

if not all_tasks:
    st.info("No tasks yet. Add one above.")
else:
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox("Filter by status", ["All", "Incomplete", "Completed"])
    with col2:
        filter_category = st.selectbox("Filter by category", ["All"] + [c.value for c in Category])

    if filter_status == "Completed":
        filtered = pet.get_tasks_by_status(True)
    elif filter_status == "Incomplete":
        filtered = pet.get_tasks_by_status(False)
    else:
        filtered = all_tasks

    if filter_category != "All":
        filtered = [t for t in filtered if t.category.value == filter_category]

    scheduler = Scheduler(owner, pet)
    sorted_tasks = scheduler.sort_by_time(filtered)

    if sorted_tasks:
        st.table([{
            "Task": t.name,
            "Category": t.category.value,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Time of Day": t.time_of_day.value if t.time_of_day else "—",
            "Frequency": t.frequency,
            "Done": "✓" if t.completed else "",
        } for t in sorted_tasks])
    else:
        st.info("No tasks match the selected filters.")

    # Warnings
    warnings = scheduler.get_warnings()
    if warnings:
        st.subheader("⚠️ Scheduling Warnings")
        for w in warnings:
            st.warning(w)

    # Cross-pet warnings (if multiple pets)
    cross_warnings = owner.detect_cross_pet_overlaps()
    if cross_warnings:
        for w in cross_warnings:
            st.warning(w)

st.divider()

# =========================================================
# SECTION 4: Generate Daily Schedule
# =========================================================
st.header("4. Today's Schedule")

if not pet.get_tasks():
    st.info("Add at least one task to generate a schedule.")
else:
    if st.button("Generate Schedule", type="primary"):
        scheduler = Scheduler(owner, pet)
        plan = scheduler.generate_plan()

        scheduled = plan["scheduled"]
        skipped = plan["skipped"]
        time_used = plan["time_used"]
        time_available = plan["time_available"]

        if scheduled:
            st.success(f"Scheduled {len(scheduled)} task(s) using {time_used} of {time_available} min.")
            st.subheader("Scheduled Tasks")
            st.table([{
                "Task": t.name,
                "Category": t.category.value,
                "Duration (min)": t.duration,
                "Priority": t.priority,
                "Time of Day": t.time_of_day.value if t.time_of_day else "—",
            } for t in scheduled])
        else:
            st.warning("No tasks could be scheduled within the available time.")

        if skipped:
            st.subheader("Skipped Tasks")
            st.caption("These tasks didn't fit within the available time.")
            st.table([{
                "Task": t.name,
                "Duration (min)": t.duration,
                "Priority": t.priority,
            } for t in skipped])

        with st.expander("View full explanation"):
            st.text(scheduler.explain_plan())

        # Time usage bar
        st.subheader("Time Usage")
        st.progress(min(time_used / time_available, 1.0),
                    text=f"{time_used} / {time_available} min used")
