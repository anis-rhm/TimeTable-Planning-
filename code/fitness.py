from code.utilities import ROOMS, TOTAL_ATTENDEES, SLOTS_PER_DAY, TOPICS, time_ordering_violated , SESSION_TYPES 



def fitness(chromosome):
    penalty = 0
    
    # Room Conflicts: Check if a room is assigned to multiple sessions at the same time
    for (topic, stype), sessions in chromosome.items():
        time_room_map = {}
        for (d, s, r, teacher) in sessions:
            if (d, s, r) in time_room_map:
                penalty += 100  # Heavy penalty for room conflicts
            else:
                time_room_map[(d, s, r)] = 1

    # Teacher Conflicts: Check if a teacher is assigned to multiple sessions at the same time
    teacher_schedule = {}
    for (topic, stype), sessions in chromosome.items():
        for (d, s, r, teacher) in sessions:
            key = (d, s)
            if key not in teacher_schedule:
                teacher_schedule[key] = set()
            if teacher in teacher_schedule[key]:
                penalty += 150  # Heavy penalty for teacher conflicts
            else:
                teacher_schedule[key].add(teacher)
    
    
    
    # Time Ordering: Theory -> Practical -> Test
    for topic in TOPICS:
        if time_ordering_violated(chromosome, topic):
            penalty += 50  # Penalty for ordering violations (Theory -> Practical -> Test)
            
            
            

    # Session Type Distribution: Balance session types
    for topic in TOPICS:
        session_count = {stype: 0 for stype in SESSION_TYPES}
        for (topic_key, stype), sessions in chromosome.items():
            if topic_key == topic:
                session_count[stype] += len(sessions)
        for stype, count in session_count.items():
            if count != 4:  # Expected to have 4 sessions for each session type
                penalty += 30 * abs(4 - count)  # Penalize under or overrepresentation




    # Time Preferences: Penalize History in the wrong slots
    for (topic, stype), sessions in chromosome.items():
        for (d, s, r, teacher) in sessions:
            if stype == "Theory" and s > 1:
                penalty += 10  # Theory should ideally be in the morning (slot 1 or 2)
            if stype == "History" and s < 2:
                penalty += 10  # History should ideally be in the evening (slot 3 or 4)




    # Check for attendees' session coverage
    attendee_sessions = {i: {topic: {stype: False for stype in SESSION_TYPES} for topic in TOPICS} for i in range(TOTAL_ATTENDEES)}
    for (topic, stype), sessions in chromosome.items():
        for (d, s, r, teacher) in sessions:
            for attendee_id in range(TOTAL_ATTENDEES):
                attendee_sessions[attendee_id][topic][stype] = True
    for attendee_id, attendance in attendee_sessions.items():
        for topic in TOPICS:
            for stype in SESSION_TYPES:
                if not attendance[topic][stype]:
                    penalty += 50  # Penalize for missing a required session





    # Penalize empty slots
    slots_used = set((d, s) for (topic, stype), sessions in chromosome.items() for (d, s, r, teacher) in sessions)
    total_slots = SLOTS_PER_DAY * len(ROOMS) * 5  # Total slots (days × slots per day × rooms)
    empty_slots = total_slots - len(slots_used)
    penalty += 40 * empty_slots  # Penalize for each empty slot



    return penalty
