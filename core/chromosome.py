import random
import logging
from collections import defaultdict
from .config import Config

logger = logging.getLogger(__name__)

class ChromosomeInitializer:
    """Enhanced chromosome initialization with conflict avoidance and diversity"""
    
    def __init__(self):
        self.initialization_attempts = 0
        self.successful_initializations = 0
    
    def initialize_chromosome(self):
        """Initialize a chromosome with better conflict avoidance"""
        self.initialization_attempts += 1
        
        chromosome = {}
        # Track assignments to avoid conflicts
        time_room_assignments = defaultdict(set)
        time_teacher_assignments = defaultdict(set)
        
        # Initialize all sessions for each topic-sessiontype combination
        for topic, stype in Config.ALL_SESSIONS:
            chromosome[(topic, stype)] = []
        
        # Assign sessions with conflict avoidance
        for topic, stype in Config.ALL_SESSIONS:
            sessions = self._assign_sessions_for_type(
                topic, stype, time_room_assignments, time_teacher_assignments
            )
            chromosome[(topic, stype)] = sessions
        
        # Validate and repair if necessary
        chromosome = self._post_process_chromosome(chromosome)
        
        self.successful_initializations += 1
        return chromosome
    
    def _assign_sessions_for_type(self, topic, stype, time_room_assignments, time_teacher_assignments):
        """Assign sessions for a specific topic and session type"""
        sessions = []
        max_attempts = 100
        
        for instance in range(Config.N_INSTANCES_PER_SESSION):
            assigned = False
            attempts = 0
            
            while not assigned and attempts < max_attempts:
                attempts += 1
                
                # Get available time slot
                day, slot = self._get_preferred_slot(topic, stype, time_room_assignments)
                time_key = (day, slot)
                
                # Find available room
                available_rooms = [
                    room for room in Config.ROOM_LIST 
                    if room not in time_room_assignments[time_key]
                ]
                
                if not available_rooms:
                    # Try different time slot
                    continue
                
                # Select appropriate room based on session type
                room = self._select_appropriate_room(stype, available_rooms)
                
                # Get available teacher
                available_teachers = [
                    teacher for teacher in Config.TOPIC_TEACHERS[topic]
                    if teacher not in time_teacher_assignments[time_key]
                ]
                
                if not available_teachers:
                    # Try different time slot
                    continue
                
                teacher = random.choice(available_teachers)
                
                # Make assignment
                sessions.append((day, slot, room, teacher))
                time_room_assignments[time_key].add(room)
                time_teacher_assignments[time_key].add(teacher)
                assigned = True
            
            # If we couldn't assign after many attempts, use fallback
            if not assigned:
                sessions.append(self._fallback_assignment(topic, stype))
        
        return sessions
    
    def _get_preferred_slot(self, topic, stype, time_room_assignments):
        """Get preferred time slot based on session type and availability"""
        preferred_slots = []
        
        # Define preferences based on session type
        if stype == "Theory":
            # Prefer morning slots (0, 1)
            preferred_slots = [(d, s) for d in range(len(Config.DAYS)) for s in [0, 1]]
        elif stype == "History":
            # Prefer afternoon slots (2, 3)
            preferred_slots = [(d, s) for d in range(len(Config.DAYS)) for s in [2, 3]]
        elif stype == "Practical":
            # Prefer middle slots (1, 2)
            preferred_slots = [(d, s) for d in range(len(Config.DAYS)) for s in [1, 2]]
        else:
            # For tests, any slot is acceptable
            preferred_slots = [(d, s) for d in range(len(Config.DAYS)) for s in range(Config.SLOTS_PER_DAY)]
        
        # Shuffle preferred slots for variety
        random.shuffle(preferred_slots)
        
        # Find slot with least conflicts
        best_slot = None
        min_conflicts = float('inf')
        
        for day, slot in preferred_slots:
            time_key = (day, slot)
            current_conflicts = len(time_room_assignments[time_key])
            
            if current_conflicts < min_conflicts:
                min_conflicts = current_conflicts
                best_slot = (day, slot)
            
            # If we find an empty slot, use it
            if current_conflicts == 0:
                break
        
        return best_slot if best_slot else Config.random_slot()
    
    def _select_appropriate_room(self, stype, available_rooms):
        """Select appropriate room based on session type"""
        if not available_rooms:
            return random.choice(Config.ROOM_LIST)
        
        # Prefer larger rooms for certain session types
        if stype in ["Theory", "Test"]:
            # Prefer amphitheater for theory and tests
            if "Amphitheater" in available_rooms:
                return "Amphitheater"
        
        # For practical sessions, prefer regular classrooms
        classroom_rooms = [room for room in available_rooms if "Classroom" in room]
        if classroom_rooms and stype == "Practical":
            return random.choice(classroom_rooms)
        
        return random.choice(available_rooms)
    
    def _fallback_assignment(self, topic, stype):
        """Fallback assignment when normal assignment fails"""
        day, slot = Config.random_slot()
        room = random.choice(Config.ROOM_LIST)
        teacher = Config.random_teacher_for_topic(topic)
        return (day, slot, room, teacher)
    
    def _post_process_chromosome(self, chromosome):
        """Post-process chromosome to improve quality"""
        # Apply time ordering heuristic
        chromosome = self._apply_time_ordering_heuristic(chromosome)
        
        # Balance session distribution
        chromosome = self._balance_session_distribution(chromosome)
        
        return chromosome
    
    def _apply_time_ordering_heuristic(self, chromosome):
        """Apply heuristic to improve time ordering"""
        for topic in Config.TOPICS:
            theory_key = (topic, "Theory")
            practical_key = (topic, "Practical")
            test_key = (topic, "Test")
            
            # Get current time slots
            theory_slots = []
            practical_slots = []
            test_slots = []
            
            if theory_key in chromosome:
                theory_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[theory_key]]
            if practical_key in chromosome:
                practical_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[practical_key]]
            if test_key in chromosome:
                test_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[test_key]]
            
            # Try to improve ordering if violated
            if theory_slots and practical_slots and min(practical_slots) <= min(theory_slots):
                self._swap_earliest_sessions(chromosome, theory_key, practical_key)
            
            if practical_slots and test_slots and min(test_slots) <= min(practical_slots):
                self._swap_earliest_sessions(chromosome, practical_key, test_key)
    
    def _swap_earliest_sessions(self, chromosome, key1, key2):
        """Swap earliest sessions between two session types"""
        if key1 not in chromosome or key2 not in chromosome:
            return
        
        sessions1 = chromosome[key1]
        sessions2 = chromosome[key2]
        
        if not sessions1 or not sessions2:
            return
        
        # Find earliest sessions
        earliest1_idx = min(range(len(sessions1)), 
                           key=lambda i: sessions1[i][0] * Config.SLOTS_PER_DAY + sessions1[i][1])
        earliest2_idx = min(range(len(sessions2)), 
                           key=lambda i: sessions2[i][0] * Config.SLOTS_PER_DAY + sessions2[i][1])
        
        # Swap time slots while keeping room and teacher
        d1, s1, r1, t1 = sessions1[earliest1_idx]
        d2, s2, r2, t2 = sessions2[earliest2_idx]
        
        sessions1[earliest1_idx] = (d2, s2, r1, t1)
        sessions2[earliest2_idx] = (d1, s1, r2, t2)
    
    def _balance_session_distribution(self, chromosome):
        """Balance session distribution across time slots"""
        # Count sessions per time slot
        slot_counts = defaultdict(int)
        
        for sessions in chromosome.values():
            for (d, s, r, t) in sessions:
                slot_counts[(d, s)] += 1
        
        # Find overloaded and underloaded slots
        if slot_counts:
            avg_load = sum(slot_counts.values()) / len(slot_counts)
            overloaded = [(slot, count) for slot, count in slot_counts.items() if count > avg_load * 1.5]
            underloaded = [(slot, count) for slot, count in slot_counts.items() if count < avg_load * 0.5]
            
            # Try to balance by moving sessions
            for overloaded_slot, _ in overloaded[:2]:  # Limit to avoid too much disruption
                for underloaded_slot, _ in underloaded[:2]:
                    if self._move_session(chromosome, overloaded_slot, underloaded_slot):
                        break
        
        return chromosome
    
    def _move_session(self, chromosome, from_slot, to_slot):
        """Move a session from one slot to another if possible"""
        from_day, from_time = from_slot
        to_day, to_time = to_slot
        
        # Find a session that can be moved
        for (topic, stype), sessions in chromosome.items():
            for i, (d, s, r, t) in enumerate(sessions):
                if (d, s) == from_slot:
                    # Check if we can move this session
                    if self._can_move_session(chromosome, (topic, stype), i, to_day, to_time):
                        sessions[i] = (to_day, to_time, r, t)
                        return True
        
        return False
    
    def _can_move_session(self, chromosome, session_key, session_idx, new_day, new_slot):
        """Check if a session can be moved to a new time slot"""
        topic, stype = session_key
        old_session = chromosome[session_key][session_idx]
        _, _, room, teacher = old_session
        
        # Check for conflicts with other sessions at the new time
        new_time_key = (new_day, new_slot)
        
        for other_sessions in chromosome.values():
            for (d, s, r, t) in other_sessions:
                if (d, s) == new_time_key:
                    if r == room or t == teacher:
                        return False  # Conflict detected
        
        return True
    
    def get_initialization_stats(self):
        """Get initialization statistics"""
        success_rate = (self.successful_initializations / self.initialization_attempts 
                       if self.initialization_attempts > 0 else 0)
        return {
            'total_attempts': self.initialization_attempts,
            'successful': self.successful_initializations,
            'success_rate': success_rate
        }