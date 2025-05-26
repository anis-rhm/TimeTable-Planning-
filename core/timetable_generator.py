import json
import csv
import logging
from datetime import datetime
from collections import defaultdict
from .config import Config

logger = logging.getLogger(__name__)

class TimetableGenerator:
    """Enhanced timetable generator with export capabilities and validation"""
    
    def __init__(self):
        self.validation_errors = []
        self.warnings = []
    
    def format_solution(self, solution):
        """Format the solution into a structured timetable with validation"""
        self.validation_errors = []
        self.warnings = []
        
        # Validate solution first
        is_valid = self._validate_solution(solution)
        
        schedule_map = defaultdict(list)
        
        for (topic, stype), sessions in solution.items():
            for (d, s, r, t) in sessions:
                key = (d, s)
                session_info = {
                    'session': f"{topic}_{stype}",
                    'room': r,
                    'teacher': t,
                    'topic': topic,
                    'type': stype,
                    'capacity': Config.ROOMS.get(r, 0),
                    'day_index': d,
                    'slot_index': s
                }
                schedule_map[key].append(session_info)
        
        # Create structured timetable
        timetable = {}
        for d, day in enumerate(Config.DAYS):
            timetable[day] = {}
            for s in range(Config.SLOTS_PER_DAY):
                slot_name = self._get_slot_name(s)
                key = (d, s)
                if key in schedule_map:
                    # Sort sessions by room for consistent display
                    sessions = sorted(schedule_map[key], key=lambda x: x['room'])
                    timetable[day][slot_name] = sessions
                else:
                    timetable[day][slot_name] = []
        
        # Add metadata
        timetable['_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'total_sessions': sum(len(sessions) for sessions in solution.values()),
            'validation_errors': self.validation_errors,
            'warnings': self.warnings,
            'is_valid': is_valid,
            'statistics': self._calculate_statistics(solution)
        }
        
        return timetable
    
    def _validate_solution(self, solution):
        """Comprehensive solution validation"""
        is_valid = True
        
        # Check for room conflicts
        room_conflicts = self._check_room_conflicts(solution)
        if room_conflicts:
            self.validation_errors.extend(room_conflicts)
            is_valid = False
        
        # Check for teacher conflicts
        teacher_conflicts = self._check_teacher_conflicts(solution)
        if teacher_conflicts:
            self.validation_errors.extend(teacher_conflicts)
            is_valid = False
        
        # Check time ordering
        ordering_issues = self._check_time_ordering_issues(solution)
        if ordering_issues:
            self.warnings.extend(ordering_issues)
        
        # Check session completeness
        completeness_issues = self._check_session_completeness(solution)
        if completeness_issues:
            self.warnings.extend(completeness_issues)
        
        return is_valid
    
    def _check_room_conflicts(self, solution):
        """Check for room scheduling conflicts"""
        conflicts = []
        time_room_map = defaultdict(list)
        
        for (topic, stype), sessions in solution.items():
            for (d, s, r, t) in sessions:
                time_room_map[(d, s, r)].append(f"{topic}_{stype}")
        
        for (d, s, r), session_list in time_room_map.items():
            if len(session_list) > 1:
                day_name = Config.DAYS[d]
                slot_name = self._get_slot_name(s)
                conflicts.append(f"Room conflict: {r} has multiple sessions at {day_name} {slot_name}: {', '.join(session_list)}")
        
        return conflicts
    
    def _check_teacher_conflicts(self, solution):
        """Check for teacher scheduling conflicts"""
        conflicts = []
        time_teacher_map = defaultdict(list)
        
        for (topic, stype), sessions in solution.items():
            for (d, s, r, t) in sessions:
                time_teacher_map[(d, s, t)].append(f"{topic}_{stype} in {r}")
        
        for (d, s, t), session_list in time_teacher_map.items():
            if len(session_list) > 1:
                day_name = Config.DAYS[d]
                slot_name = self._get_slot_name(s)
                conflicts.append(f"Teacher conflict: {t} has multiple sessions at {day_name} {slot_name}: {', '.join(session_list)}")
        
        return conflicts
    
    def _check_time_ordering_issues(self, solution):
        """Check for time ordering constraint violations"""
        issues = []
        
        for topic in Config.TOPICS:
            theory_times = []
            practical_times = []
            test_times = []
            
            if (topic, "Theory") in solution:
                theory_times = [d * Config.SLOTS_PER_DAY + s for (d, s, r, t) in solution[(topic, "Theory")]]
            if (topic, "Practical") in solution:
                practical_times = [d * Config.SLOTS_PER_DAY + s for (d, s, r, t) in solution[(topic, "Practical")]]
            if (topic, "Test") in solution:
                test_times = [d * Config.SLOTS_PER_DAY + s for (d, s, r, t) in solution[(topic, "Test")]]
            
            if theory_times and practical_times and min(practical_times) <= min(theory_times):
                issues.append(f"Topic {topic}: Practical sessions should come after Theory sessions")
            
            if practical_times and test_times and min(test_times) <= min(practical_times):
                issues.append(f"Topic {topic}: Test sessions should come after Practical sessions")
        
        return issues
    
    def _check_session_completeness(self, solution):
        """Check if all required sessions are present"""
        issues = []
        
        for topic in Config.TOPICS:
            for stype in Config.SESSION_TYPES:
                key = (topic, stype)
                if key not in solution or not solution[key]:
                    issues.append(f"Missing sessions for {topic} {stype}")
                elif len(solution[key]) != Config.N_INSTANCES_PER_SESSION:
                    expected = Config.N_INSTANCES_PER_SESSION
                    actual = len(solution[key])
                    issues.append(f"Incorrect number of {topic} {stype} sessions: expected {expected}, got {actual}")
        
        return issues
    
    def _calculate_statistics(self, solution):
        """Calculate timetable statistics"""
        stats = {
            'total_sessions': 0,
            'sessions_by_type': defaultdict(int),
            'sessions_by_topic': defaultdict(int),
            'room_utilization': defaultdict(int),
            'teacher_workload': defaultdict(int),
            'slots_used': set(),
            'days_used': set()
        }
        
        for (topic, stype), sessions in solution.items():
            stats['total_sessions'] += len(sessions)
            stats['sessions_by_type'][stype] += len(sessions)
            stats['sessions_by_topic'][topic] += len(sessions)
            
            for (d, s, r, t) in sessions:
                stats['room_utilization'][r] += 1
                stats['teacher_workload'][t] += 1
                stats['slots_used'].add((d, s))
                stats['days_used'].add(d)
        
        # Convert sets to counts for JSON serialization
        stats['unique_slots_used'] = len(stats['slots_used'])
        stats['unique_days_used'] = len(stats['days_used'])
        del stats['slots_used']
        del stats['days_used']
        
        # Convert defaultdicts to regular dicts
        stats['sessions_by_type'] = dict(stats['sessions_by_type'])
        stats['sessions_by_topic'] = dict(stats['sessions_by_topic'])
        stats['room_utilization'] = dict(stats['room_utilization'])
        stats['teacher_workload'] = dict(stats['teacher_workload'])
        
        return stats
    
    def _get_slot_name(self, slot_index):
        """Get readable slot name with time ranges"""
        slot_times = {
            0: "08:00 - 10:00 (Morning)",
            1: "10:30 - 12:30 (Late Morning)", 
            2: "13:30 - 15:30 (Afternoon)",
            3: "16:00 - 18:00 (Evening)"
        }
        return slot_times.get(slot_index, f"Slot {slot_index + 1}")
    
    def export_to_json(self, timetable, filename=None):
        """Export timetable to JSON format"""
        if filename is None:
            filename = f"timetable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(timetable, f, indent=2, ensure_ascii=False)
            logger.info(f"Timetable exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to export timetable to JSON: {str(e)}")
            raise
    
    def export_to_csv(self, timetable, filename=None):
        """Export timetable to CSV format"""
        if filename is None:
            filename = f"timetable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Day', 'Time Slot', 'Session', 'Topic', 'Type', 'Room', 'Teacher', 'Capacity'])
                
                # Data rows
                for day, slots in timetable.items():
                    if day == '_metadata':
                        continue
                    
                    for slot_time, sessions in slots.items():
                        if sessions:
                            for session in sessions:
                                writer.writerow([
                                    day,
                                    slot_time,
                                    session['session'],
                                    session['topic'],
                                    session['type'],
                                    session['room'],
                                    session['teacher'],
                                    session['capacity']
                                ])
                        else:
                            writer.writerow([day, slot_time, 'No sessions', '', '', '', '', ''])
            
            logger.info(f"Timetable exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to export timetable to CSV: {str(e)}")
            raise
    
    def generate_summary_report(self, timetable):
        """Generate a comprehensive summary report"""
        metadata = timetable.get('_metadata', {})
        stats = metadata.get('statistics', {})
        
        report = []
        report.append("=" * 80)
        report.append("TIMETABLE SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {metadata.get('generated_at', 'Unknown')}")
        report.append(f"Valid: {'Yes' if metadata.get('is_valid', False) else 'No'}")
        report.append(f"Total Sessions: {stats.get('total_sessions', 0)}")
        report.append("")
        
        # Validation results
        errors = metadata.get('validation_errors', [])
        warnings = metadata.get('warnings', [])
        
        if errors:
            report.append("VALIDATION ERRORS:")
            for error in errors:
                report.append(f"  ❌ {error}")
            report.append("")
        
        if warnings:
            report.append("WARNINGS:")
            for warning in warnings:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        # Statistics
        report.append("STATISTICS:")
        report.append(f"  Sessions by Type:")
        for stype, count in stats.get('sessions_by_type', {}).items():
            report.append(f"    {stype}: {count}")
        
        report.append(f"  Sessions by Topic:")
        for topic, count in stats.get('sessions_by_topic', {}).items():
            report.append(f"    {topic}: {count}")
        
        report.append(f"  Room Utilization:")
        for room, count in stats.get('room_utilization', {}).items():
            utilization_pct = (count / 20) * 100  # 20 = 5 days * 4 slots
            report.append(f"    {room}: {count} sessions ({utilization_pct:.1f}%)")
        
        report.append(f"  Teacher Workload:")
        for teacher, count in stats.get('teacher_workload', {}).items():
            report.append(f"    {teacher}: {count} sessions")
        
        report.append("")
        report.append(f"  Time Slots Used: {stats.get('unique_slots_used', 0)}")
        report.append(f"  Days Used: {stats.get('unique_days_used', 0)}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def print_solution(self, solution, cost=None):
        """Print the timetable in an enhanced readable format"""
        timetable = self.format_solution(solution)
        metadata = timetable.get('_metadata', {})
        
        print("\n" + "=" * 100)
        print("🎓 UNIVERSITY TIMETABLE SYSTEM")
        print("=" * 100)
        
        if cost is not None:
            print(f"📊 Solution Quality Score: {cost}")
        
        print(f"✅ Validation Status: {'VALID' if metadata.get('is_valid', False) else 'INVALID'}")
        print(f"📅 Generated: {metadata.get('generated_at', 'Unknown')}")
        print(f"📈 Total Sessions: {metadata.get('statistics', {}).get('total_sessions', 0)}")
        
        # Show validation issues if any
        errors = metadata.get('validation_errors', [])
        warnings = metadata.get('warnings', [])
        
        if errors:
            print(f"\n❌ VALIDATION ERRORS ({len(errors)}):")
            for error in errors[:3]:  # Show first 3 errors
                print(f"   • {error}")
            if len(errors) > 3:
                print(f"   ... and {len(errors) - 3} more errors")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings[:3]:  # Show first 3 warnings
                print(f"   • {warning}")
            if len(warnings) > 3:
                print(f"   ... and {len(warnings) - 3} more warnings")
        
        print("-" * 100)
        
        for day, slots in timetable.items():
            if day == '_metadata':
                continue
                
            print(f"\n{'🗓️  ' + day.upper():^100}")
            print("=" * 100)
            
            for slot_time, sessions in slots.items():
                print(f"\n🕐 {slot_time}")
                print("-" * 80)
                
                if sessions:
                    for session in sessions:
                        capacity_info = f" (Capacity: {session['capacity']})" if session['capacity'] > 0 else ""
                        print(f"  📚 {session['session']} | 🏛️  {session['room']}{capacity_info} | 👨‍🏫 {session['teacher']}")
                else:
                    print("  💤 No sessions scheduled")
        
        print("\n" + "=" * 100)
        
        # Print summary statistics
        stats = metadata.get('statistics', {})
        if stats:
            print("\n📊 SUMMARY STATISTICS:")
            print("-" * 50)
            room_util = stats.get('room_utilization', {})
            most_used_room = max(room_util.items(), key=lambda x: x[1]) if room_util else None
            if most_used_room:
                print(f"🏆 Most utilized room: {most_used_room[0]} ({most_used_room[1]} sessions)")
            
            teacher_load = stats.get('teacher_workload', {})
            busiest_teacher = max(teacher_load.items(), key=lambda x: x[1]) if teacher_load else None
            if busiest_teacher:
                print(f"👩‍🏫 Busiest teacher: {busiest_teacher[0]} ({busiest_teacher[1]} sessions)")
            
            print(f"📅 Days utilized: {stats.get('unique_days_used', 0)}/{len(Config.DAYS)}")
            print(f"⏰ Time slots utilized: {stats.get('unique_slots_used', 0)}/{len(Config.DAYS) * Config.SLOTS_PER_DAY}")
        
        print("=" * 100)