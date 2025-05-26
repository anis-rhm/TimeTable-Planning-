from code.utilities import DAYS, SLOTS_PER_DAY

# Function to print the beautiful timetable 
def print_solution(solution, cost=None):
    schedule_map = {}
    for (topic, stype), sessions in solution.items():
        for (d, s, r, t) in sessions:
            key = (d, s)
            if key not in schedule_map:
                schedule_map[key] = []
            session_name = f"{topic}_{stype}"
            schedule_map[key].append((session_name, r, t))

    slot_str_map = {
        0: "Slot 1 (8:00 - 10:00)",
        1: "Slot 2 (10:30 - 12:30)",
        2: "Slot 3 (13:30 - 15:30)",
        3: "Slot 4 (16:00 - 18:00)"
    }

    # Print the schedule in a clean and organized way
    print("\n" + "=" * 50)
    print("Schedule Overview:")
    print("=" * 50)

    # Print the cost if available
    if cost is not None:
        print(f"Cost for this solution: {cost}")
    
    for d, day in enumerate(DAYS):
        print(f"\n=== {day} ===")
        for s in range(SLOTS_PER_DAY):
            key = (d, s)
            print(f"\n{slot_str_map[s]}:", end=" ")
            if key in schedule_map:
                sessions = schedule_map[key]
                for session_name, room, teacher in sessions:
                    print(f"{session_name} (Room: {room}, Teacher: {teacher})", end="; ")
                print()  # New line after all sessions in the slot
            else:
                print("No Sessions")
        print("-" * 50)  # Separator after each day

    print("=" * 50 + "\n")  # End separator
