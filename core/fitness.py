import logging
from collections import defaultdict
from .config import Config

logger = logging.getLogger(__name__)

class FitnessEvaluator:
    """Enhanced fitness evaluator with weighted constraints and caching"""
    
    def __init__(self):
        # Constraint weights for fine-tuning optimization priorities
        self.weights = {
            'room_conflicts': 1000,      # Critical - cannot have room conflicts
            'teacher_conflicts': 800,    # Critical - cannot have teacher conflicts
            'time_ordering': 300,        # Important - educational sequence
            'session_distribution': 200, # Important - balanced scheduling
            'time_preferences': 100,     # Moderate - quality improvement
            'session_coverage': 150,     # Important - all students covered
            'room_utilization': 50,      # Low - efficiency optimization
            'teacher_workload': 75       # Moderate - fair distribution
        }
        
        # Cache for performance
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def fitness(self, chromosome):
        """Calculate enhanced fitness penalty with weighted constraints"""
        # Create a hash key for caching (simplified)
        cache_key = self._create_cache_key(chromosome)
        
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        penalty = 0
        
        # Critical constraints (must be satisfied)
        penalty += self.weights['room_conflicts'] * self._check_room_conflicts(chromosome)
        penalty += self.weights['teacher_conflicts'] * self._check_teacher_conflicts(chromosome)
        
        # Important constraints (strong preference)
        penalty += self.weights['time_ordering'] * self._check_time_ordering(chromosome)
        penalty += self.weights['session_distribution'] * self._check_session_distribution(chromosome)
        penalty += self.weights['session_coverage'] * self._check_session_coverage(chromosome)
        
        # Quality improvement constraints
        penalty += self.weights['time_preferences'] * self._check_time_preferences(chromosome)
        penalty += self.weights['room_utilization'] * self._check_room_utilization(chromosome)
        penalty += self.weights['teacher_workload'] * self._check_teacher_workload(chromosome)
        
        # Additional soft constraints
        penalty += self._check_day_distribution(chromosome)
        penalty += self._check_consecutive_sessions(chromosome)
        
        # Cache the result
        self._cache[cache_key] = penalty
        
        # Limit cache size to prevent memory issues
        if len(self._cache) > 10000:
            # Remove oldest 20% of entries
            items_to_remove = list(self._cache.keys())[:2000]
            for key in items_to_remove:
                del self._cache[key]
        
        return penalty
    
    def _create_cache_key(self, chromosome):
        """Create a simple hash key for caching"""
        # This is a simplified approach - in practice, you might want a more sophisticated hash
        key_parts = []
        for (topic, stype) in sorted(Config.ALL_SESSIONS):
            if (topic, stype) in chromosome:
                sessions = sorted(chromosome[(topic, stype)])
                key_parts.append(f"{topic}_{stype}_{len(sessions)}")
        return "_".join(key_parts[:10])  # Limit length
    
    def _check_room_conflicts(self, chromosome):
        """Optimized room conflict detection"""
        time_room_map = defaultdict(set)
        conflicts = 0
        
        for sessions in chromosome.values():
            for (d, s, r, teacher) in sessions:
                time_key = (d, s)
                if r in time_room_map[time_key]:
                    conflicts += 1
                time_room_map[time_key].add(r)
        
        return conflicts
    
    def _check_teacher_conflicts(self, chromosome):
        """Optimized teacher conflict detection"""
        time_teacher_map = defaultdict(set)
        conflicts = 0
        
        for sessions in chromosome.values():
            for (d, s, r, teacher) in sessions:
                time_key = (d, s)
                if teacher in time_teacher_map[time_key]:
                    conflicts += 1
                time_teacher_map[time_key].add(teacher)
        
        return conflicts
    
    def _check_time_ordering(self, chromosome):
        """Enhanced time ordering constraint with partial credit"""
        penalty = 0
        
        for topic in Config.TOPICS:
            theory_slots = []
            practical_slots = []
            test_slots = []
            
            # Collect time slots for each session type
            if (topic, "Theory") in chromosome:
                theory_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[(topic, "Theory")]]
            if (topic, "Practical") in chromosome:
                practical_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[(topic, "Practical")]]
            if (topic, "Test") in chromosome:
                test_slots = [(d * Config.SLOTS_PER_DAY + s) for (d, s, r, t) in chromosome[(topic, "Test")]]
            
            # Check ordering violations
            if theory_slots and practical_slots:
                if min(practical_slots) <= min(theory_slots):
                    penalty += 1
            
            if practical_slots and test_slots:
                if min(test_slots) <= min(practical_slots):
                    penalty += 1
            
            if theory_slots and test_slots:
                if min(test_slots) <= min(theory_slots):
                    penalty += 0.5  # Less severe if practical is missing
        
        return penalty
    
    def _check_session_distribution(self, chromosome):
        """Check balanced distribution of sessions"""
        penalty = 0
        topic_session_counts = defaultdict(lambda: defaultdict(int))
        
        for (topic, stype), sessions in chromosome.items():
            topic_session_counts[topic][stype] = len(sessions)
        
        # Each topic should have roughly equal number of each session type
        expected_sessions_per_type = Config.N_INSTANCES_PER_SESSION
        
        for topic in Config.TOPICS:
            for stype in Config.SESSION_TYPES:
                actual_count = topic_session_counts[topic][stype]
                deviation = abs(actual_count - expected_sessions_per_type)
                penalty += deviation * 0.5
        
        return penalty
    
    def _check_time_preferences(self, chromosome):
        """Enhanced time preferences with graduated penalties"""
        penalty = 0
        
        for (topic, stype), sessions in chromosome.items():
            for (d, s, r, teacher) in sessions:
                # Morning preference for Theory (slots 0, 1)
                if stype == "Theory":
                    if s >= 2:
                        penalty += 0.3 * (s - 1)  # Graduated penalty
                
                # Afternoon preference for History (slots 2, 3)
                elif stype == "History":
                    if s < 2:
                        penalty += 0.3 * (2 - s)
                
                # Practical sessions better in middle slots
                elif stype == "Practical":
                    if s == 0 or s == 3:
                        penalty += 0.2
        
        return penalty
    
    def _check_session_coverage(self, chromosome):
        """Simplified session coverage check"""
        penalty = 0
        
        # Check that each topic has all required session types
        for topic in Config.TOPICS:
            for stype in Config.SESSION_TYPES:
                if (topic, stype) not in chromosome or not chromosome[(topic, stype)]:
                    penalty += 10  # Missing session type for topic
        
        return penalty
    
    def _check_room_utilization(self, chromosome):
        """Check efficient room utilization"""
        penalty = 0
        room_usage = defaultdict(int)
        total_sessions = 0
        
        for sessions in chromosome.values():
            for (d, s, r, teacher) in sessions:
                room_usage[r] += 1
                total_sessions += 1
        
        if total_sessions > 0:
            # Penalize uneven room usage
            avg_usage = total_sessions / len(Config.ROOM_LIST)
            for room, usage in room_usage.items():
                deviation = abs(usage - avg_usage)
                penalty += deviation * 0.1
        
        return penalty
    
    def _check_teacher_workload(self, chromosome):
        """Check balanced teacher workload"""
        penalty = 0
        teacher_workload = defaultdict(int)
        
        for sessions in chromosome.values():
            for (d, s, r, teacher) in sessions:
                teacher_workload[teacher] += 1
        
        if teacher_workload:
            workloads = list(teacher_workload.values())
            avg_workload = sum(workloads) / len(workloads)
            
            for workload in workloads:
                deviation = abs(workload - avg_workload)
                penalty += deviation * 0.05
        
        return penalty
    
    def _check_day_distribution(self, chromosome):
        """Ensure sessions are distributed across days"""
        penalty = 0
        day_usage = defaultdict(int)
        
        for sessions in chromosome.values():
            for (d, s, r, teacher) in sessions:
                day_usage[d] += 1
        
        if day_usage:
            usages = list(day_usage.values())
            avg_usage = sum(usages) / len(usages)
            
            for usage in usages:
                deviation = abs(usage - avg_usage)
                penalty += deviation * 0.03
        
        return penalty
    
    def _check_consecutive_sessions(self, chromosome):
        """Penalize too many consecutive sessions for same topic"""
        penalty = 0
        
        for topic in Config.TOPICS:
            topic_sessions = []
            for stype in Config.SESSION_TYPES:
                if (topic, stype) in chromosome:
                    for (d, s, r, teacher) in chromosome[(topic, stype)]:
                        topic_sessions.append((d, s))
            
            # Sort by time
            topic_sessions.sort(key=lambda x: x[0] * Config.SLOTS_PER_DAY + x[1])
            
            # Check for too many consecutive slots
            consecutive_count = 1
            for i in range(1, len(topic_sessions)):
                prev_time = topic_sessions[i-1][0] * Config.SLOTS_PER_DAY + topic_sessions[i-1][1]
                curr_time = topic_sessions[i][0] * Config.SLOTS_PER_DAY + topic_sessions[i][1]
                
                if curr_time == prev_time + 1:
                    consecutive_count += 1
                    if consecutive_count > 2:  # More than 2 consecutive sessions
                        penalty += 0.2
                else:
                    consecutive_count = 1
        
        return penalty
    
    def get_cache_stats(self):
        """Get cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(self._cache)
        }