import random
from code.utilities import random_slot, random_teacher_for_topic, ROOM_LIST, N_INSTANCES_PER_SESSION, ALL_SESSIONS

def initialize_chromosome():
    """Initialize a random chromosome with diverse and independent assignments."""
    chromosome = {}
    all_room_assignments = set()  
    
    for _ in ALL_SESSIONS:  # Iterate over all session types and topics
        
        # Randomly select a tuple from ALL_SESSIONS
        topic, stype = random.choice(ALL_SESSIONS)

        # Randomly assign day and slot for the selected session type and topic
        day, slot = random_slot()

        rooms = ROOM_LIST[:]
        random.shuffle(rooms)  # Shuffle the rooms list to ensure randomness
        
        chosen_rooms = rooms[:N_INSTANCES_PER_SESSION]  # Select the required number of rooms

        # Initialize an empty list for the topic and session type
        chromosome[(topic, stype)] = []

        # Assign rooms, teachers, and sessions while ensuring no overlapping room assignments
        for i in range(N_INSTANCES_PER_SESSION):
            room = chosen_rooms[i]
            teacher = random_teacher_for_topic(topic)
            
            # Ensure the room, day, and slot combination is unique
            while (day, slot, room) in all_room_assignments:
                day, slot = random_slot()  # Pick a new time slot if there's a conflict
            all_room_assignments.add((day, slot, room))  # Add the new room assignment to the set

            # Add the assignment (day, slot, room, teacher) to the chromosome for the current topic and session type
            chromosome[(topic, stype)].append((day, slot, room, teacher))

    return chromosome
