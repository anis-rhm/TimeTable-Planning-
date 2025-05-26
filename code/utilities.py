import random

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

SLOTS_PER_DAY = 4

SLOTS = ['S1', 'S2' , 'S3' , 'S4']

TOTAL_ATTENDEES = 600

ROOMS = {
    "Classroom1": 60,
    "Classroom2": 60,
    "Classroom3": 60,
    "Classroom4": 60,
    "Classroom5": 60,
    "Amphitheater": 180
}

ROOM_LIST = list(ROOMS.keys())


N_INSTANCES_PER_SESSION = len(ROOMS)

SESSION_TYPES = ["Theory", "Practical", "History", "Test"]

TOPICS = ["A", "B", "C", "D"]

ALL_SESSIONS = [(topic, stype) for topic in TOPICS for stype in SESSION_TYPES]

TOPIC_TEACHERS = {
    "A": ["A1", "A2"],
    "B": ["B1", "B2"],
    "C": ["C1", "C2"],
    "D": ["D1", "D2"]
}



def random_teacher_for_topic(topic):
    return random.choice(TOPIC_TEACHERS[topic])

def random_slot():
    d = random.randint(0, len(DAYS)-1)       #chooses random day
    s = random.randint(0, SLOTS_PER_DAY-1)   #chooses random slot
    return d, s



#in this code we check the constraint Theory -> Practical -> Test 
#in here we noted the Test with x
def time_ordering_violated(chromosome, topic):
    def slot_key(x): return x[0] * SLOTS_PER_DAY + x[1]

    # Check if Theory, Practical, and Test exist for the topic
    if (topic, "Theory") not in chromosome or (topic, "Practical") not in chromosome or (topic, "Test") not in chromosome:
        return False  # No violation if any session type is missing

    t_slots = sorted([(d, s) for (d, s, r, t) in chromosome[(topic, "Theory")]], key=slot_key)
    p_slots = sorted([(d, s) for (d, s, r, t) in chromosome[(topic, "Practical")]], key=slot_key)
    x_slots = sorted([(d, s) for (d, s, r, t) in chromosome[(topic, "Test")]], key=slot_key)

    if not t_slots or not p_slots or not x_slots:
        return True

    earliest_T = t_slots[0]
    earliest_P = p_slots[0]
    earliest_X = x_slots[0]

    if slot_key(earliest_P) <= slot_key(earliest_T):
        return True
    if slot_key(earliest_X) <= slot_key(earliest_P):
        return True
    return False
