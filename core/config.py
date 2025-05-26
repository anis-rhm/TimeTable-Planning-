import random
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class Config:
    """Enhanced configuration with validation and flexible settings"""
    
    # Basic schedule structure
    DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    SLOTS_PER_DAY = 4
    SLOTS = ['S1', 'S2', 'S3', 'S4']
    TOTAL_ATTENDEES = 600

    # Room configuration with capacity and type information
    ROOMS = {
        "Classroom1": {"capacity": 60, "type": "standard", "equipment": ["projector", "whiteboard"]},
        "Classroom2": {"capacity": 60, "type": "standard", "equipment": ["projector", "whiteboard"]},
        "Classroom3": {"capacity": 60, "type": "standard", "equipment": ["projector", "whiteboard"]},
        "Classroom4": {"capacity": 60, "type": "standard", "equipment": ["projector", "whiteboard"]},
        "Classroom5": {"capacity": 60, "type": "standard", "equipment": ["projector", "whiteboard"]},
        "Amphitheater": {"capacity": 180, "type": "lecture", "equipment": ["projector", "microphone", "recording"]}
    }

    # Legacy compatibility - room capacities only
    ROOM_CAPACITIES = {name: info["capacity"] if isinstance(info, dict) else info 
                      for name, info in ROOMS.items()}

    ROOM_LIST = list(ROOMS.keys())
    N_INSTANCES_PER_SESSION = len(ROOMS)
    
    # Topics and their requirements
    TOPICS = ["A", "B", "C", "D"]
    TOPIC_INFO = {
        "A": {"name": "Mathematics", "difficulty": "high", "prerequisites": []},
        "B": {"name": "Physics", "difficulty": "high", "prerequisites": ["A"]},
        "C": {"name": "Chemistry", "difficulty": "medium", "prerequisites": []},
        "D": {"name": "Biology", "difficulty": "medium", "prerequisites": ["C"]}
    }
    
    # Session types with preferences
    SESSION_TYPES = ["Theory", "Practical", "History", "Test"]
    SESSION_TYPE_PREFERENCES = {
        "Theory": {
            "preferred_slots": [0, 1],  # Morning slots
            "preferred_rooms": ["Amphitheater", "Classroom1", "Classroom2"],
            "min_duration": 120,  # minutes
            "requires_equipment": ["projector"]
        },
        "Practical": {
            "preferred_slots": [1, 2],  # Mid-day slots
            "preferred_rooms": ["Classroom3", "Classroom4", "Classroom5"],
            "min_duration": 120,
            "requires_equipment": ["projector", "whiteboard"]
        },
        "History": {
            "preferred_slots": [2, 3],  # Afternoon slots
            "preferred_rooms": ["Classroom1", "Classroom2"],
            "min_duration": 120,
            "requires_equipment": ["projector"]
        },
        "Test": {
            "preferred_slots": [0, 1, 2, 3],  # Any slot
            "preferred_rooms": ["Amphitheater"],  # Large room for tests
            "min_duration": 120,
            "requires_equipment": []
        }
    }
    
    # All possible session combinations (defined after SESSION_TYPES)
    ALL_SESSIONS = [(topic, stype) for topic in TOPICS for stype in SESSION_TYPES]

    # Teacher assignments with expertise and availability
    TOPIC_TEACHERS = {
        "A": {
            "A1": {"expertise": ["Theory", "Test"], "max_hours_per_day": 6, "unavailable_slots": []},
            "A2": {"expertise": ["Practical", "History"], "max_hours_per_day": 6, "unavailable_slots": []}
        },
        "B": {
            "B1": {"expertise": ["Theory", "Test"], "max_hours_per_day": 6, "unavailable_slots": []},
            "B2": {"expertise": ["Practical", "History"], "max_hours_per_day": 6, "unavailable_slots": []}
        },
        "C": {
            "C1": {"expertise": ["Theory", "Test"], "max_hours_per_day": 6, "unavailable_slots": []},
            "C2": {"expertise": ["Practical", "History"], "max_hours_per_day": 6, "unavailable_slots": []}
        },
        "D": {
            "D1": {"expertise": ["Theory", "Test"], "max_hours_per_day": 6, "unavailable_slots": []},
            "D2": {"expertise": ["Practical", "History"], "max_hours_per_day": 6, "unavailable_slots": []}
        }
    }
    
    # Legacy compatibility - simple teacher list per topic
    TOPIC_TEACHERS_SIMPLE = {
        topic: list(teachers.keys()) for topic, teachers in TOPIC_TEACHERS.items()
    }

    # Constraint weights for optimization
    CONSTRAINT_WEIGHTS = {
        "hard_constraints": {
            "room_conflicts": 1000,
            "teacher_conflicts": 800,
            "capacity_violations": 500
        },
        "soft_constraints": {
            "time_ordering": 300,
            "teacher_preferences": 200,
            "room_preferences": 150,
            "balanced_distribution": 100,
            "consecutive_sessions": 50
        }
    }

    # Time preferences
    TIME_PREFERENCES = {
        "morning_start": 8,  # 8 AM
        "lunch_break": (12, 13),  # 12-1 PM
        "evening_end": 18,  # 6 PM
        "slot_duration": 120  # 2 hours per slot
    }

    @classmethod
    def validate_configuration(cls) -> List[str]:
        """Validate the configuration and return any errors"""
        errors = []
        
        # Validate basic structure
        if len(cls.DAYS) == 0:
            errors.append("No days defined")
        
        if cls.SLOTS_PER_DAY <= 0:
            errors.append("Invalid slots per day")
        
        if len(cls.ROOMS) == 0:
            errors.append("No rooms defined")
        
        # Validate rooms
        for room_name, room_info in cls.ROOMS.items():
            if isinstance(room_info, dict):
                if "capacity" not in room_info:
                    errors.append(f"Room {room_name} missing capacity")
                elif room_info["capacity"] <= 0:
                    errors.append(f"Room {room_name} has invalid capacity")
        
        # Validate topics and teachers
        for topic in cls.TOPICS:
            if topic not in cls.TOPIC_TEACHERS:
                errors.append(f"No teachers defined for topic {topic}")
            elif len(cls.TOPIC_TEACHERS[topic]) == 0:
                errors.append(f"No teachers available for topic {topic}")
        
        # Validate session types
        for stype in cls.SESSION_TYPES:
            if stype not in cls.SESSION_TYPE_PREFERENCES:
                errors.append(f"No preferences defined for session type {stype}")
        
        # Validate total capacity
        total_capacity = sum(
            (room_info["capacity"] if isinstance(room_info, dict) else room_info)
            for room_info in cls.ROOMS.values()
        )
        if total_capacity < cls.TOTAL_ATTENDEES:
            errors.append(f"Total room capacity ({total_capacity}) less than total attendees ({cls.TOTAL_ATTENDEES})")
        
        return errors

    @staticmethod
    def random_teacher_for_topic(topic: str, session_type: Optional[str] = None) -> str:
        """Get a random teacher for a topic, optionally filtered by session type expertise"""
        if topic not in Config.TOPIC_TEACHERS:
            logger.warning(f"Topic {topic} not found in TOPIC_TEACHERS")
            return f"{topic}1"  # Fallback
        
        available_teachers = []
        
        for teacher_name, teacher_info in Config.TOPIC_TEACHERS[topic].items():
            # Check if teacher has expertise for this session type
            if session_type and isinstance(teacher_info, dict):
                expertise = teacher_info.get("expertise", [])
                if session_type not in expertise:
                    continue
            available_teachers.append(teacher_name)
        
        # Fallback to any teacher if no expertise match
        if not available_teachers:
            available_teachers = list(Config.TOPIC_TEACHERS[topic].keys())
        
        return random.choice(available_teachers) if available_teachers else f"{topic}1"

    @staticmethod
    def random_slot() -> Tuple[int, int]:
        """Get a random time slot (day_index, slot_index)"""
        d = random.randint(0, len(Config.DAYS) - 1)
        s = random.randint(0, Config.SLOTS_PER_DAY - 1)
        return d, s

    @staticmethod
    def get_preferred_slots_for_session_type(session_type: str) -> List[int]:
        """Get preferred time slots for a session type"""
        preferences = Config.SESSION_TYPE_PREFERENCES.get(session_type, {})
        return preferences.get("preferred_slots", list(range(Config.SLOTS_PER_DAY)))

    @staticmethod
    def get_preferred_rooms_for_session_type(session_type: str) -> List[str]:
        """Get preferred rooms for a session type"""
        preferences = Config.SESSION_TYPE_PREFERENCES.get(session_type, {})
        preferred = preferences.get("preferred_rooms", Config.ROOM_LIST)
        # Filter to only include rooms that exist
        return [room for room in preferred if room in Config.ROOM_LIST]

    @staticmethod
    def is_teacher_available(teacher: str, topic: str, day: int, slot: int) -> bool:
        """Check if a teacher is available at a specific time"""
        if topic not in Config.TOPIC_TEACHERS:
            return True
        
        teacher_info = Config.TOPIC_TEACHERS[topic].get(teacher, {})
        if not isinstance(teacher_info, dict):
            return True
        
        unavailable_slots = teacher_info.get("unavailable_slots", [])
        return (day, slot) not in unavailable_slots

    @staticmethod
    def get_room_capacity(room: str) -> int:
        """Get the capacity of a room"""
        room_info = Config.ROOMS.get(room, {})
        if isinstance(room_info, dict):
            return room_info.get("capacity", 0)
        return room_info if isinstance(room_info, int) else 0

    @staticmethod
    def get_room_equipment(room: str) -> List[str]:
        """Get equipment available in a room"""
        room_info = Config.ROOMS.get(room, {})
        if isinstance(room_info, dict):
            return room_info.get("equipment", [])
        return []

    @staticmethod
    def check_room_suitable_for_session(room: str, session_type: str) -> bool:
        """Check if a room is suitable for a session type"""
        preferences = Config.SESSION_TYPE_PREFERENCES.get(session_type, {})
        required_equipment = preferences.get("requires_equipment", [])
        
        if not required_equipment:
            return True
        
        room_equipment = Config.get_room_equipment(room)
        return all(equipment in room_equipment for equipment in required_equipment)

    @staticmethod
    def time_ordering_violated(chromosome: Dict, topic: str) -> bool:
        """Check if time ordering constraint is violated (Theory -> Practical -> Test)"""
        def slot_key(x: Tuple[int, int]) -> int: 
            return x[0] * Config.SLOTS_PER_DAY + x[1]

        theory_key = (topic, "Theory")
        practical_key = (topic, "Practical") 
        test_key = (topic, "Test")

        if not all(key in chromosome for key in [theory_key, practical_key, test_key]):
            return False

        theory_sessions = chromosome.get(theory_key, [])
        practical_sessions = chromosome.get(practical_key, [])
        test_sessions = chromosome.get(test_key, [])

        if not all([theory_sessions, practical_sessions, test_sessions]):
            return True

        # Get earliest time for each session type
        theory_times = [(d, s) for (d, s, r, t) in theory_sessions]
        practical_times = [(d, s) for (d, s, r, t) in practical_sessions]
        test_times = [(d, s) for (d, s, r, t) in test_sessions]

        earliest_theory = min(theory_times, key=slot_key) if theory_times else None
        earliest_practical = min(practical_times, key=slot_key) if practical_times else None
        earliest_test = min(test_times, key=slot_key) if test_times else None

        # Check ordering: Theory < Practical < Test
        if earliest_theory and earliest_practical:
            if slot_key(earliest_practical) <= slot_key(earliest_theory):
                return True

        if earliest_practical and earliest_test:
            if slot_key(earliest_test) <= slot_key(earliest_practical):
                return True

        return False

    @staticmethod
    def get_slot_time_range(slot_index: int) -> Tuple[int, int]:
        """Get the time range for a slot (start_hour, end_hour)"""
        start_times = [8, 10.5, 13.5, 16]  # Start times for each slot
        if 0 <= slot_index < len(start_times):
            start = start_times[slot_index]
            end = start + 2  # 2-hour slots
            return int(start), int(end) if end == int(end) else int(end) + 0.5
        return 8, 10  # Default

    @classmethod
    def print_configuration_summary(cls):
        """Print a summary of the current configuration"""
        print("\n" + "=" * 60)
        print("TIMETABLE SYSTEM CONFIGURATION")
        print("=" * 60)
        print(f"📅 Days: {', '.join(cls.DAYS)}")
        print(f"⏰ Slots per day: {cls.SLOTS_PER_DAY}")
        print(f"👥 Total attendees: {cls.TOTAL_ATTENDEES}")
        
        print(f"\n🏛️  Rooms ({len(cls.ROOMS)}):")
        for room, info in cls.ROOMS.items():
            if isinstance(info, dict):
                capacity = info.get("capacity", "Unknown")
                room_type = info.get("type", "standard")
                equipment = ", ".join(info.get("equipment", []))
                print(f"  • {room}: {capacity} capacity, {room_type} ({equipment})")
            else:
                print(f"  • {room}: {info} capacity")
        
        print(f"\n📚 Topics ({len(cls.TOPICS)}):")
        for topic in cls.TOPICS:
            topic_info = cls.TOPIC_INFO.get(topic, {})
            name = topic_info.get("name", topic)
            difficulty = topic_info.get("difficulty", "unknown")
            teachers = list(cls.TOPIC_TEACHERS.get(topic, {}).keys())
            print(f"  • {topic} ({name}): {difficulty} difficulty, {len(teachers)} teachers")
        
        print(f"\n🎯 Session Types ({len(cls.SESSION_TYPES)}):")
        for stype in cls.SESSION_TYPES:
            prefs = cls.SESSION_TYPE_PREFERENCES.get(stype, {})
            preferred_slots = prefs.get("preferred_slots", [])
            print(f"  • {stype}: preferred slots {preferred_slots}")
        
        print(f"\n📊 Total possible sessions: {len(cls.ALL_SESSIONS)}")
        
        # Validation
        errors = cls.validate_configuration()
        if errors:
            print(f"\n❌ Configuration Errors ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
        else:
            print(f"\n✅ Configuration is valid")
        
        print("=" * 60)