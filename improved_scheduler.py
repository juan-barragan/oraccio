# %%
import pandas as pd
import numpy as np
from collections import defaultdict, namedtuple

# Define the schedule entry structure
ScheduleEntry = namedtuple('ScheduleEntry', ['class_name', 'teacher', 'subject'])

class ImprovedSchoolScheduler:
    MAX_DAILY_HOURS_FOR_TEACHER = 5
    MIN_HOURS_FOR_TEACHER = 2
    MINIMUM_FOR_AVAILABILITY = MAX_DAILY_HOURS_FOR_TEACHER - MIN_HOURS_FOR_TEACHER
    MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS = 2

    ALLOWED_14 = {
        'LUN': ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L'],
        'MER': ['1L', '1I', '2L', '2I', '3L'],
        'VEN': ['3L']
    }

    def __init__(self, csv_file_path):
        """
        Initialize the scheduler with the cleaned CSV file.
        
        Args:
            csv_file_path: Path to the conseil_docente_cleaned.csv file
        """
        self.csv_file_path = csv_file_path
        
        # School schedule parameters
        self.days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
        self.hours = list(range(8, 15))  # 8:00 AM to 2:00 PM (7 hours per day)
        
        # Load and prepare data
        self.load_data()
        
        # Initialize empty schedule
        self.schedule = self.create_empty_schedule()
        self.teacher_assignments = defaultdict(int)  # Track assigned hours per teacher
        self.class_assignments = defaultdict(int)    # Track assigned hours per class
        
    def max_hours_allowed(self, day, class_name):
        """Return the maximum hours allowed for a class on a given day."""
        if day == 'MAR' or day == 'GIO':
            return 7
        else:
            if class_name in ImprovedSchoolScheduler.ALLOWED_14.get(day, []):
                return 7    
            return 6

    def load_data(self):
        """Load and prepare the teacher-class data from CSV."""
        df = pd.read_csv(self.csv_file_path)
        
        # Remove rows with missing data
        df = df.dropna(subset=['Identificativo', 'Materia', 'Classi', 'N.Ore'])
        
        # Convert N.Ore to integer
        df['N.Ore'] = df['N.Ore'].astype(int)
        
        # Store the data
        self.conseil_docente = df
        
        # Create assignment dictionary: {(teacher, class, subject): hours_needed}
        self.assignments = {}
        self.teacher_total_hours = defaultdict(int)
        self.class_total_hours = defaultdict(int)
        
        for _, row in df.iterrows():
            teacher = row['Identificativo']
            class_name = row['Classi']
            subject = row['Materia']
            hours = row['N.Ore']
            
            # Use teacher-class-subject as key to handle multiple subjects per teacher-class
            key = (teacher, class_name, subject)
            self.assignments[key] = hours
            
            # Track total hours per teacher and class
            self.teacher_total_hours[teacher] += hours
            self.class_total_hours[class_name] += hours
            
        # Get unique teachers and classes
        self.teachers = sorted(df['Identificativo'].unique())
        self.classes = sorted(df['Classi'].unique())
        self.subjects = sorted(df['Materia'].unique())
        
    def create_empty_schedule(self):
        """Create an empty schedule structure."""
        schedule = {}
        for day in self.days:
            schedule[day] = {}
            for hour in self.hours:
                schedule[day][hour] = []  # List of ScheduleEntry objects
        return schedule
        
    def get_teacher_hours_on_day(self, teacher, day):
        """Count how many hours a teacher is scheduled on a specific day."""
        count = 0
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.teacher == teacher:
                    count += 1
        return count
        
    def get_class_hours_on_day(self, class_name, day):
        """Count how many hours a class is scheduled on a specific day."""
        count = 0
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.class_name == class_name:
                    count += 1
        return count

    def get_teacher_hours_for_class(self, teacher, class_name, day):
        """Get the hours a teacher is teaching a specific class on a specific day."""
        count = 0
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.teacher == teacher and entry.class_name == class_name:
                    count += 1
        return count

    def professor_availability_on_day(self, teacher, day):
        """Get the hours a teacher is available on a specific day."""
        scheduled_hours = set()
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.teacher == teacher:
                    scheduled_hours.add(hour)
        return list(set(self.hours) - scheduled_hours)
    
    def professor_availability(self, teacher):
        """Get the full availability of a teacher across all days."""
        availability = {}
        for day in self.days:
            availability_on_day = self.professor_availability_on_day(teacher, day)
            if len(availability_on_day) > 0:
                availability[day] = availability_on_day
        return availability


    def is_slot_available(self, teacher, class_name, day, hour):
        """
        Check if a time slot is available for a teacher-class assignment.
        
        Returns:
            bool: True if slot is available, False otherwise
        """
        if day in ImprovedSchoolScheduler.ALLOWED_14 and hour == 14:
            if class_name not in ImprovedSchoolScheduler.ALLOWED_14[day]:
                return False
                
        # Check if teacher is already teaching at this time
        for entry in self.schedule[day][hour]:
            if entry.teacher == teacher:
                return False
                
        # Check if class already has a lesson at this time
        for entry in self.schedule[day][hour]:
            if entry.class_name == class_name:
                return False
            
        # Check teacher's daily workload (max 5 hours per day)
        if self.get_teacher_hours_on_day(teacher, day) >= 5:
            return False
            
        # Check class daily workload except those allowed at 14:00
        max_hours = self.max_hours_allowed(day, class_name)
        if self.get_class_hours_on_day(class_name, day) >= max_hours:
            return False
        
        # Check if teacher-class combination already has 2 hours on this day (max 2 hours per day)
        teacher_class_hours_today = 0
        for h in self.hours:
            for entry in self.schedule[day][h]:
                if entry.class_name == class_name and entry.teacher == teacher:
                    teacher_class_hours_today += 1
        
        if teacher_class_hours_today >= self.MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS:
            return False
            
        return True

    def get_available_slots(self, teacher, class_name) -> list[tuple]:
        """Get all available slots for a teacher-class combination."""
        available = []
        for day in self.days:
            for hour in self.hours:
                if self.is_slot_available(teacher, class_name, day, hour):
                    available.append((day, hour))
        return available
        
    def when_professor_is_teaching_class(self, teacher, class_name):
        """Get all time slots when a professor is teaching a specific class."""
        teaching_slots = defaultdict(list)
        for day in self.days:
            for hour in self.hours:
                for entry in self.schedule[day][hour]:
                    if entry.teacher == teacher and entry.class_name == class_name:
                        teaching_slots[day].append(hour)
        return teaching_slots
        
    
    def assign_slot(self, teacher, class_name, subject, day, hour):
        """Assign a slot and update tracking."""
        entry = ScheduleEntry(class_name=class_name, teacher=teacher, subject=subject)
        self.schedule[day][hour].append(entry)
        self.teacher_assignments[teacher] += 1
        self.class_assignments[class_name] += 1
        
    def create_schedule(self):
        """
        Create the complete school schedule using a constraint-aware algorithm.
        
        Returns:
            tuple: (success_rate, allocated_hours, total_hours)
        """
        print("Creating school schedule...")
        
        # Sort assignments by difficulty (fewer available slots = higher priority)
        assignment_priority = []
        for (teacher, class_name, subject), hours_needed in self.assignments.items():
            available_slots = len(self.get_available_slots(teacher, class_name))
            # Priority: hours_needed / available_slots ratio (higher = more urgent)
            if available_slots > 0:
                priority = hours_needed / available_slots
            else:
                priority = float('inf')  # Impossible assignments get highest priority
            assignment_priority.append((priority, teacher, class_name, subject, hours_needed))
            
        # Sort by priority (highest first)
        assignment_priority.sort(reverse=True, key=lambda x: x[0])
        
        allocated_hours = 0
        total_hours = sum(self.assignments.values())
        failed_assignments = []
        
        print(f"Processing {len(assignment_priority)} assignments...")
        
        # Process each assignment
        for i, (priority, teacher, class_name, subject, hours_needed) in enumerate(assignment_priority):
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(assignment_priority)} assignments...")
                
            hours_allocated = 0
            
            # Try to allocate all hours for this assignment
            for attempt in range(hours_needed):
                available_slots = self.get_available_slots(teacher, class_name)
                
                if available_slots:
                    # Choose a slot (prefer morning hours)
                    best_slot = None
                    best_score = -1
                    
                    for day, hour in available_slots:
                        score = 0
                        # Prefer morning hours
                        if hour <= 11:
                            score += 10
                        # Prefer creating blocks for teacher
                        teacher_adjacent = 0
                        for adj_hour in [hour-1, hour+1]:
                            if adj_hour in self.hours:
                                for entry in self.schedule[day][adj_hour]:
                                    if entry.teacher == teacher:
                                        teacher_adjacent += 1
                        score += teacher_adjacent * 5
                        
                        if score > best_score:
                            best_score = score
                            best_slot = (day, hour)
                    
                    if best_slot:
                        day, hour = best_slot
                        self.assign_slot(teacher, class_name, subject, day, hour)
                        hours_allocated += 1
                        allocated_hours += 1
                    else:
                        break
                else:
                    # No available slots
                    break
            
            # Track failed assignments
            if hours_allocated < hours_needed:
                remaining_hours = hours_needed - hours_allocated
                failed_assignments.append((teacher, class_name, subject, remaining_hours, hours_allocated))
        
        success_rate = (allocated_hours / total_hours) * 100
        
        print(f"\nSchedule creation completed!")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Allocated hours: {allocated_hours}/{total_hours}")
        
        if failed_assignments:
            print(f"\nFailed to fully allocate {len(failed_assignments)} assignments:")
            for teacher, class_name, subject, remaining, allocated in failed_assignments[:15]:
                print(f"  {teacher} - {class_name} ({subject}): {allocated}/{allocated + remaining} hours allocated")
            if len(failed_assignments) > 15:
                print(f"  ... and {len(failed_assignments) - 15} more")
        
            self.failed_assignments = pd.DataFrame(failed_assignments, columns=['teacher', 'class_name', 'subject', 'remaining', 'allocated'])
        
        return success_rate, allocated_hours, total_hours

    def save_failed_assignments(self, output_file='failed.txt'):
        """Save failed assignments to a text file."""
        self.failed_assignments.to_csv(output_file, index=False)
    
    def schedule_to_dataframe(self):
        """Convert the schedule to pandas DataFrames for easy viewing."""
        # Create teacher schedule DataFrame
        teacher_data = []
        for teacher in self.teachers:
            row = {'Teacher': teacher}
            total_hours = 0
            for day in self.days:
                daily_hours = 0
                for hour in self.hours:
                    col = f"{day}{hour}"
                    # Find what this teacher teaches at this time
                    teaching = []
                    for entry in self.schedule[day][hour]:
                        if entry.teacher == teacher:
                            teaching.append(f"{entry.class_name}")
                            daily_hours += 1
                            total_hours += 1
                    row[col] = ', '.join(teaching) if teaching else ''
            row['Weekly_Total'] = total_hours
            teacher_data.append(row)
            
        teacher_df = pd.DataFrame(teacher_data)
        teacher_df.set_index('Teacher', inplace=True)
        
        # Create class schedule DataFrame
        class_data = []
        for class_name in self.classes:
            row = {'Class': class_name}
            total_hours = 0
            for day in self.days:
                daily_hours = 0
                for hour in self.hours:
                    col = f"{day}_{hour:02d}h"
                    # Find if this class is scheduled at this time
                    class_entry = None
                    for entry in self.schedule[day][hour]:
                        if entry.class_name == class_name:
                            class_entry = entry
                            break
                    
                    if class_entry:
                        row[col] = f"{class_entry.teacher}({class_entry.subject})"
                        daily_hours += 1
                        total_hours += 1
                    else:
                        row[col] = ''
                row[f'{day}_total'] = daily_hours
            row['Weekly_Total'] = total_hours
            class_data.append(row)
            
        class_df = pd.DataFrame(class_data)
        class_df.set_index('Class', inplace=True)
        
        return teacher_df, class_df
    
    def schedule_slot_to_dataframe(self, day, hour):
        """
        Transform a specific schedule slot (day, hour) to a pandas DataFrame.
        
        Args:
            day: Day of the week (e.g., 'LUN', 'MAR', etc.)
            hour: Hour of the day (8-14)
        
        Returns:
            pandas.DataFrame: DataFrame with columns ['class_name', 'teacher', 'subject']
        """
        entries = self.schedule[day][hour]
        
        if not entries:
            # Return empty DataFrame with proper columns if no entries
            return pd.DataFrame(columns=['class_name', 'teacher', 'subject'])
        
        # Convert list of ScheduleEntry namedtuples to DataFrame
        data = []
        for entry in entries:
            data.append({
                'class_name': entry.class_name,
                'teacher': entry.teacher,
                'subject': entry.subject
            })
        
        return pd.DataFrame(data)
    
    def get_full_schedule_dataframe(self):
        """
        Convert the entire schedule to a single pandas DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame with columns ['day', 'hour', 'class_name', 'teacher', 'subject']
        """
        all_data = []
        
        for day in self.days:
            for hour in self.hours:
                for entry in self.schedule[day][hour]:
                    all_data.append({
                        'day': day,
                        'hour': hour,
                        'class_name': entry.class_name,
                        'teacher': entry.teacher,
                        'subject': entry.subject
                    })
        
        return pd.DataFrame(all_data)
    
    def teacher_free_slots_on_day(self, teacher, day):
        """Get a list of free time slots for a teacher on a specific day."""

        scheduled_hours = set()
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.teacher == teacher:
                    scheduled_hours.add(hour)
        return [hour for hour in self.hours if hour not in scheduled_hours]

    def who_is_teaching_class_at(self, class_name, day, hour):
        """Return the teacher and subject teaching a class at a specific time."""
        for entry in self.schedule[day][hour]:
            if entry.class_name == class_name:
                return entry.teacher, entry.subject
        return None, None

    def who_teaches_class_on_day(self, class_name, day):
        """Return a list of teachers teaching a class on a specific day."""
        teachers = set()
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.class_name == class_name:
                    teachers.add( (entry.teacher, hour))
        return list(teachers)
    
    def sanity_check_schedule(self):
        """Perform sanity checks on the schedule to ensure constraints are met."""
        for day in self.days:
            for hour in self.hours:
                # Check for teacher double-booking
                teachers_this_hour = [entry.teacher for entry in self.schedule[day][hour]]
                if len(teachers_this_hour) != len(set(teachers_this_hour)):
                    teacher_counts = {}
                    for teacher in teachers_this_hour:
                        teacher_counts[teacher] = teacher_counts.get(teacher, 0) + 1
                    for teacher, count in teacher_counts.items():
                        if count > 1:
                            print(f"⛔️Sanity check failed: Teacher {teacher} double-booked at {day} {hour}:00")
                            return False
                
                # Check for class double-booking
                classes_this_hour = [entry.class_name for entry in self.schedule[day][hour]]
                if len(classes_this_hour) != len(set(classes_this_hour)):
                    class_counts = {}
                    for class_name in classes_this_hour:
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1
                    for class_name, count in class_counts.items():
                        if count > 1:
                            print(f"⛔️Sanity check failed: Class {class_name} double-booked at {day} {hour}:00")
                            return False
                
                # Check individual constraints for each entry
                for entry in self.schedule[day][hour]:
                    # Check daily limits for teacher
                    if self.get_teacher_hours_on_day(entry.teacher, day) > 5:
                        print(f"⛔️Sanity check failed: Teacher {entry.teacher} exceeds daily limit on {day}")
                        return False
                    
                    # Check daily limits for class
                    max_hours = self.max_hours_allowed(day, entry.class_name)
                    if self.get_class_hours_on_day(entry.class_name, day) > max_hours:
                        print(f"⛔️Sanity check failed: Class {entry.class_name} exceeds daily limit on {day}")
                        return False
                    
                    # Check teacher-class combination limit
                    teacher_class_hours_today = 0
                    for h in self.hours:
                        for e in self.schedule[day][h]:
                            if e.class_name == entry.class_name and e.teacher == entry.teacher:
                                teacher_class_hours_today += 1
                    
                    if teacher_class_hours_today > self.MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS:
                        print(f"⛔️Sanity check failed: Teacher {entry.teacher} exceeds class limit for {entry.class_name} on {day}")
                        return False
        
        print("✅Sanity check passed: Schedule meets all constraints.")
        return True
    
    def swap_class_for_professor(self, day1, hour1, day2, hour2, professor):
        """Swap classes for a given professor between two time slots."""
        entry1 = None
        entry2 = None
        
        # Find entries taught by the professor in the specified slots
        for entry in self.schedule[day1][hour1]:
            if entry.teacher == professor:
                entry1 = entry
                break
                
        for entry in self.schedule[day2][hour2]:
            if entry.teacher == professor:
                entry2 = entry
                break
                
        if entry1 and entry2:
            # Perform the swap
            self.schedule[day1][hour1].remove(entry1)
            self.schedule[day2][hour2].remove(entry2)
            
            # Create new entries with swapped positions
            new_entry1 = ScheduleEntry(entry2.class_name, professor, entry2.subject)
            new_entry2 = ScheduleEntry(entry1.class_name, professor, entry1.subject)
            
            self.schedule[day1][hour1].append(new_entry1)
            self.schedule[day2][hour2].append(new_entry2)
            return True
        
        # Handle case where only one entry is found
        if entry1 and not entry2:
            self.schedule[day1][hour1].remove(entry1)
            new_entry = ScheduleEntry(entry1.class_name, professor, entry1.subject)
            self.schedule[day2][hour2].append(new_entry)
            return True
            
        if entry2 and not entry1:
            self.schedule[day2][hour2].remove(entry2)
            new_entry = ScheduleEntry(entry2.class_name, professor, entry2.subject)
            self.schedule[day1][hour1].append(new_entry)
            return True
            
        return False

    def get_max_classes_at(self, day, hour):
        """Get the maximum allowed classes at a specific day and hour."""
        if hour <= 13 or day not in ImprovedSchoolScheduler.ALLOWED_14:
            return self.classes
        else:
            return ImprovedSchoolScheduler.ALLOWED_14[day]
        
    def max_num_classes_at(self, day, hour):
        """Get the maximum number of classes allowed at a specific day and hour."""
        return len(self.get_max_classes_at(day, hour))

    def missing_classes_on_schedule(self):
        """Find missing classes that should be scheduled but aren't."""
        missing_classes = defaultdict(list)
        for day in self.days:
            for hour in self.hours:
                scheduled_classes = {entry.class_name for entry in self.schedule[day][hour]}
                max_classes_set = set(self.get_max_classes_at(day, hour))
                
                if len(scheduled_classes) < len(max_classes_set):
                    missing_classes[(day, hour)] = list(max_classes_set - scheduled_classes)
        return missing_classes

    def is_teacher_free_at(self, teacher, day, hour):
        """Check if a teacher is free at a specific day and hour."""
        for entry in self.schedule[day][hour]:
            if entry.teacher == teacher:
                return False
        return True
    
    def who_can_swap_with_professor(self, day, hour, professor):
        """Find teachers who can swap classes with a given professor at a specific time."""
        can_swap = []
        # Find available slots for the professor on that day
        prof_free_slots = self.professor_availability_on_day(professor, day)
        class_name, _ = self.what_class_is_taught_by_teacher_at(professor, day, hour)
        # Find professors teaching class_name on prof_free_slots free at day, hour
        for h in prof_free_slots:
            teacher, _ = self.who_is_teaching_class_at(class_name, day, h)
            if teacher and self.is_teacher_free_at(teacher, day, hour):
                can_swap.append((teacher, h))

        return can_swap

    def what_class_is_taught_by_teacher_at(self, teacher, day, hour):
        """Return the class and subject taught by a teacher at a specific time."""
        for entry in self.schedule[day][hour]:
            if entry.teacher == teacher:
                return entry.class_name, entry.subject
        return None, None

    def who_is_available_to_teach_class(self, class_name):
        """Find teachers available to teach a specific class from failed assignments."""
        available_teachers = self.failed_assignments[
            self.failed_assignments['class_name'] == class_name
        ][['teacher', 'subject']].values.tolist()

        return available_teachers

    def update_failed_assignments(self, teacher, class_name, subject, hours_allocated):
        """Update the failed assignments DataFrame after allocating hours."""
        mask = (
            (self.failed_assignments['teacher'] == teacher) &
            (self.failed_assignments['class_name'] == class_name) &
            (self.failed_assignments['subject'] == subject)
        )
        
        if not self.failed_assignments[mask].empty:
            idx = self.failed_assignments[mask].index[0]
            self.failed_assignments.at[idx, 'allocated'] += hours_allocated
            self.failed_assignments.at[idx, 'remaining'] -= hours_allocated
            
            if self.failed_assignments.at[idx, 'remaining'] <= 0:
                self.failed_assignments = self.failed_assignments.drop(idx).reset_index(drop=True)
                
    def is_swap_feasible(self, day1, hour1, day2, hour2, professor):
        """Check if swapping classes for a professor between two time slots is feasible."""
        entry1 = None
        entry2 = None
        
        # Find entries taught by the professor in the specified slots
        for entry in self.schedule[day1][hour1]:
            if entry.teacher == professor:
                entry1 = entry
                break
                
        for entry in self.schedule[day2][hour2]:
            if entry.teacher == professor:
                entry2 = entry
                break
                
        # Check feasibility of swap
        if entry1 and entry2:
            # Check if swapping would violate constraints
            if not self.is_slot_available(professor, entry2.class_name, day1, hour1):
                return False
            if not self.is_slot_available(professor, entry1.class_name, day2, hour2):
                return False
            return True
        
        # If only one entry exists, check if moving it is feasible
        if entry1 and not entry2:
            if not self.is_slot_available(professor, entry1.class_name, day2, hour2):
                return False
            return True
            
        if entry2 and not entry1:
            if not self.is_slot_available(professor, entry2.class_name, day1, hour1):
                return False
            return True
            
        return False
    
    def save_schedule(self, output_dir='./'):
        """Save the schedule to CSV files."""
        teacher_df, class_df = self.schedule_to_dataframe()
        
        teacher_file = f"{output_dir}improved_teacher_schedule.csv"
        class_file = f"{output_dir}improved_class_schedule.csv"
        
        teacher_df.to_csv(teacher_file)
        class_df.to_csv(class_file)
        
        print(f"\nSchedule saved:")
        print(f"  Teacher schedule: {teacher_file}")
        print(f"  Class schedule: {class_file}")
        
        return teacher_file, class_file

    def what_is_professor_teaching_at(self, teacher, day):
        """Return the subject a professor is teaching at a specific day."""
        subjects = []
        for hour in self.hours:
            for entry in self.schedule[day][hour]:
                if entry.teacher == teacher:
                    subjects.append((hour, entry.class_name, entry.subject))
        return subjects
    
# Main execution
scheduler = ImprovedSchoolScheduler('/Users/juan/Projects/oraccio/data/conseil_docente_cleaned.csv')
success_rate, allocated, total = scheduler.create_schedule()
# scheduler.save_schedule('/Users/juan/Projects/oraccio/')

# %%
def insert_missing_classes_into_schedule(scheduler):
    missing_classes = scheduler.missing_classes_on_schedule()
    for (day, hour), class_list in sorted(missing_classes.items()):
        for class_missing in class_list:
            available_profs = scheduler.who_is_available_to_teach_class(class_missing)
            # Filter out professors with already 5 hurs on that day
            available_profs = [
                (prof, subject) for prof, subject in available_profs
                               if scheduler.get_teacher_hours_on_day(prof, day) < 5
            ]
            if available_profs:
                # Among available profs, find one who can swap
                teachers = None
                for prof, subject in available_profs:
                    teachers = scheduler.who_can_swap_with_professor(day, hour, prof)
                    if teachers:
                        break

                if teachers:
                    print(teachers)
                    # TODO: find the closest hour to minimize disruption
                    closest_hour = min(teachers, key=lambda x: abs(x[1] - hour))
                    teacher, h = closest_hour
                    scheduler.swap_class_for_professor(day, hour, day, h, teacher)
                    scheduler.swap_class_for_professor(day, h, day, hour, prof)
                    # prof can receive the class at (day, hour) now
                    scheduler.assign_slot(prof, class_missing, subject, day, hour)
                    scheduler.update_failed_assignments(prof, class_missing, subject, 1)
                    clean = scheduler.sanity_check_schedule()
                    if not clean:
                        print("Schedule became invalid after insertion!")
                        return
                        
# insert_missing_classes_into_schedule(scheduler)

# %%
def insert_missing_classes_into_schedule_second_stage(scheduler):
    missing_classes = scheduler.missing_classes_on_schedule()
    for (day, hour), class_list in sorted(missing_classes.items()):
        for class_missing in class_list:
            print(f"Looking for available professors for class {class_missing} on {day} at {hour}:00")
            available_profs = scheduler.who_is_available_to_teach_class(class_missing)
            if available_profs:
                for available_prof, subject in available_profs:
                    print(f"  Checking available professor {available_prof}")
                    # What classes is prof teaching on that slot?
                    class_name, _ = scheduler.what_class_is_taught_by_teacher_at(available_prof, day, hour)
                    prof_available_slots = scheduler.professor_availability(available_prof)
                    # Look at the class counsil to find who can teach the class
                    conseil = scheduler.conseil_docente[scheduler.conseil_docente['Classi'] == class_name]  
                    could_take_on = [
                        prof for prof in conseil['Identificativo']
                        if scheduler.is_teacher_free_at(prof, day, hour) and
                        scheduler.get_teacher_hours_on_day(prof, day) < 5 and
                        scheduler.get_teacher_hours_for_class(prof, class_name, day) < scheduler.MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS
                    ]
                    done = False
                    for prof_could_take_on in could_take_on:
                        time_table = scheduler.when_professor_is_teaching_class(prof_could_take_on, class_name)
                        # Find the first common slot
                        for d, hours in time_table.items():
                            for h in hours:
                                if h in prof_available_slots.get(d, []):
                                    print(f"Freeing {available_prof} at {day} {hour}:00 by moving class {class_name} to {d} {h}:00")
                                    scheduler.swap_class_for_professor(day, hour, d, h, available_prof)
                                    print(f"Moving class {class_name} of {prof_could_take_on} from {d} {h}:00 to {day} {hour}:00")
                                    scheduler.swap_class_for_professor(d, h, day, hour, prof_could_take_on)
                                    print(f"Assigning class {class_missing} to {available_prof} at {day} {hour}:00")
                                    scheduler.assign_slot(available_prof, class_missing, subject, day, hour)
                                    scheduler.update_failed_assignments(available_prof, class_missing, subject, 1)
                                    clean = scheduler.sanity_check_schedule()
                                    if not clean:
                                        print("Schedule became invalid after insertion!")
                                        return
                                    # scheduler.assign_slot(prof_could_take_on, class_name, _, d, h)
                                    done = True
                                    break
                            if done:
                                break
                        if done:
                            break

# insert_missing_classes_into_schedule_second_stage(scheduler)

# %%
def insert_missing_classes_into_schedule_third_stage(scheduler):
    missing_classes = scheduler.missing_classes_on_schedule()
    for (missing_day, missing_hour), class_list in sorted(missing_classes.items()):
        for class_missing in class_list:
            print(f"Looking for available professors for class {class_missing} on {missing_day} at {missing_hour}:00")
            available_profs = scheduler.who_is_available_to_teach_class(class_missing)
            slot_assigned = False
            for available_prof, available_subject in available_profs:
                teacher_work = scheduler.what_is_professor_teaching_at(available_prof, missing_day)
                teacher_availability = scheduler.professor_availability(available_prof)
                # wipe out day where theacher is working already 5 hours or more
                teacher_availability = {day: hours for day, hours in teacher_availability.items() if len(hours) > 2}
                print(teacher_availability)
                # look on the teachers council to see who can take on the classes
                for hour, class_name, subject in teacher_work:
                    conseil = scheduler.conseil_docente[scheduler.conseil_docente['Classi'] == class_name]
                    available_teachers = conseil[conseil['Identificativo'] != available_prof]
                    available_teachers = [
                        prof for prof in available_teachers['Identificativo']
                        if scheduler.is_teacher_free_at(prof, missing_day, hour) and
                        scheduler.get_teacher_hours_on_day(prof, missing_day) < 5 and
                        scheduler.get_teacher_hours_for_class(prof, class_name, missing_day) < 2
                    ]
                    # Find a teacher who can switch
                    for prof in available_teachers:
                        
                        # When is prof teaching class_name?
                        time_table = scheduler.when_professor_is_teaching_class(prof, class_name)
                        for d, hours in time_table.items():
                            for h in hours:
                                if h in teacher_availability.get(d, []):
                                    print(f"Freeing {available_prof} by moving {class_name} {missing_day} {hour}:00 by to {d} {h}:00")
                                    scheduler.swap_class_for_professor(missing_day, hour, d, h, available_prof)
                                    print(f"Moving class {class_name} of {prof} from {d} {h}:00 to {missing_day} {hour}:00")
                                    scheduler.swap_class_for_professor(d, h, missing_day, hour, prof)
                                    # Assign class to {available_prof}.
                                    print(f"Assigning class {class_missing} to {available_prof} at {missing_day} {missing_hour}:00")
                                    scheduler.assign_slot(available_prof, class_missing, subject, missing_day, missing_hour)
                                    scheduler.update_failed_assignments(available_prof, class_missing, available_subject, 1)
                                    clean = scheduler.sanity_check_schedule()
                                    if not clean:
                                        print("Schedule became invalid after insertion!")
                                        # revert changes?
                                        return
                                    slot_assigned = True
                                    break
                            if slot_assigned:
                                break
                        if slot_assigned:
                                break
                    if slot_assigned:
                        break
                if slot_assigned:
                    break
            if slot_assigned:
                break

# insert_missing_classes_into_schedule_third_stage(scheduler)

# %%
def who_can_free_me_up_by_swaping_class(scheduler, day, hour, professor):
    """Find teachers who can free up a professor at day, hour by swapping that class on other slots."""
    # What is teaching at that slot?
    class_name, _ = scheduler.what_class_is_taught_by_teacher_at(professor, day, hour)
    # What's teacher availability on other days?
    prof_available_slots = scheduler.professor_available_slots(professor)
    # Who is teaching that class on other days?
    for d, hours in prof_available_slots.items():
        for h in hours:
            teacher, _ = scheduler.who_is_teaching_class_at(class_name, d, h)
            if teacher and scheduler.is_teacher_free_at(teacher, day, hour) and can_teacher_teach_class_on_slot(scheduler, teacher, class_name, day, hour):
                return (teacher, d, h)
    return None

def can_teacher_teach_class_on_slot(scheduler, teacher, class_name, day, hour):
    """Check if a teacher can teach a class on a specific slot."""
    # Is teacher free at that slot?
    if not scheduler.is_teacher_free_at(teacher, day, hour):
        return False
    # Does teacher have less than 5 hours on that day?
    if scheduler.get_teacher_hours_on_day(teacher, day) >= scheduler.MAX_DAILY_HOURS_FOR_TEACHER:
        return False
    # Does teacher have less than allowed max hours for that class on that day?
    if scheduler.get_teacher_hours_for_class(teacher, class_name, day) >= scheduler.MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS:
        return False
    return True

def when_professor_is_teaching_class_on_day(scheduler, professor, class_name, day):
    """Find the time slots when a professor is teaching a specific class on a specific day."""
    hours_taught = []
    for hour in scheduler.hours:
        for entry in scheduler.schedule[day][hour]:
            if entry.teacher == professor and entry.class_name == class_name:
                hours_taught.append(hour)
    return hours_taught

def professors_teaching_class_on_slots(scheduler, class_name, slots):
    """Find professors teaching a specific class on given slots."""
    professors = {}
    for day in slots:
        for hour in slots[day]:
            for entry in scheduler.schedule[day][hour]:
                if entry.class_name == class_name:
                    if entry.teacher not in professors:
                        professors[entry.teacher] = []
                    professors[entry.teacher].append((day, hour))
    return professors

def can_professors_swap_same_class(scheduler, prof1, day1, hour1, prof2, day2, hour2):
    """Check if two professors can swap classes on given slots."""
    class1, _ = scheduler.what_class_is_taught_by_teacher_at(prof1, day1, hour1)
    class2, _ = scheduler.what_class_is_taught_by_teacher_at(prof2, day2, hour2)
    if class1 != class2:
        return False
    if not can_teacher_teach_class_on_slot(scheduler, prof1, class1, day2, hour2):
        return False
    if not can_teacher_teach_class_on_slot(scheduler, prof2, class2, day1, hour1):
        return False
    return True

def swap_strategy_for_max_num_class_on_day(scheduler, professor, day, class_name):
    # Professor is teaching max number of hours on that day for that class
    # Goal is to free up one slot by swapping with other professors teaching that class on other days
    # 1. find when professor is teaching that class on this day (hours)
    hours_professor_is_teaching_class = when_professor_is_teaching_class_on_day(scheduler, professor, class_name, day)
    # 2. find other professors teaching that class on the free slots of the professor, differents from current day
    availability_professor = scheduler.professor_availability(professor)
    other_professors = professors_teaching_class_on_slots(scheduler, class_name, availability_professor)
    # 3. among these professors, find one who can receive the class on any day (hours) for the professor          
    for other_prof in other_professors:
        if not scheduler.is_teacher_free_at(other_prof, day, hour):
            continue
        for hour in hours_professor_is_teaching_class:
            for d, h2 in other_professors[other_prof]:
                if can_teacher_teach_class_on_slot(scheduler, other_prof, class_name, day, hour):
                    print(f"Swapping {d} from {d} {h2}:00 to {day} {hour}:00 to free up {professor}")
                    scheduler.swap_class_for_professor(day, hour, d, h2, other_prof)
                    print(f"Swapping {professor} from {day} {hour}:00 to {d} {h2}:00")
                    scheduler.swap_class_for_professor(d, h2, day, hour, professor)
                    return True
    return False

def swap_strategy_for_being_busy_on_slot(scheduler, professor, day, hour):
    # Professor is busy at that slot
    # Goal is to free up that slot by swapping with other professors teaching other classes on other days
    class_name, _ = scheduler.what_class_is_taught_by_teacher_at(professor, day, hour)
    # 1. find other professors teaching that class on the free slots of the professor, differents from current day
    availability_professor = scheduler.professor_availability(professor)
    other_professors = professors_teaching_class_on_slots(scheduler, class_name, availability_professor)
    # 2. among these professors, find one who can receive the class on (day, hour)          
    for other_prof in other_professors:
        # other_prof should be free at (day, hour)
        if not scheduler.is_teacher_free_at(other_prof, day, hour):
            continue
        for d, h2 in other_professors[other_prof]:
            if d != day:
                if not can_teacher_teach_class_on_slot(scheduler, other_prof, class_name, day, hour):
                    continue
            if can_teacher_teach_class_on_slot(scheduler, professor, class_name, d, h2):
                print(f"Swapping {d} from {d} {h2}:00 to {day} {hour}:00 to free up {professor}")
                scheduler.swap_class_for_professor(day, hour, d, h2, other_prof)
                print(f"Swapping {professor} from {day} {hour}:00 to {d} {h2}:00")
                scheduler.swap_class_for_professor(d, h2, day, hour, professor)
                return True
    return False

def swap_strategy_for_fully_booked(scheduler, available_prof, day):
    # Professor is fully booked on that day
    # Goal is to free up one slot by swapping with other professors teaching other classes on other days
    classes_professor_is_teaching = scheduler.what_is_professor_teaching_at(available_prof, day)
    for h, class_name, subject in classes_professor_is_teaching:
        availability_professor = scheduler.professor_availability(available_prof)
        other_professors = professors_teaching_class_on_slots(scheduler, class_name, availability_professor)
        for other_prof in other_professors:
            for d, h2 in other_professors[other_prof]:
                if scheduler.is_teacher_free_at(other_prof, day, h)\
                    and can_teacher_teach_class_on_slot(scheduler, other_prof, class_name, day, h)\
                    and can_teacher_teach_class_on_slot(scheduler, available_prof, class_name, d, h2):
                    print(f"Swapping {d} from {d} {h2}:00 to {day} {h}:00 to free up {available_prof}")
                    scheduler.swap_class_for_professor(day, h, d, h2, other_prof)
                    print(f"Swapping {available_prof} from {day} {h}:00 to {d} {h2}:00")
                    scheduler.swap_class_for_professor(d, h2, day, h, available_prof)
                    return True
    return False

def insert_missing_classes_via_swap_strategy(scheduler):
    missing_classes = scheduler.missing_classes_on_schedule()
    for (day, hour), class_list in sorted(missing_classes.items()):
        for class_missing in sorted(class_list):
            print(f"Looking for available professors for class {class_missing} on {day} at {hour}:00")
            available_profs = scheduler.who_is_available_to_teach_class(class_missing)
            for available_prof, available_subject in sorted(available_profs):
                # Can prof receive the class directly?
                if scheduler.get_teacher_hours_for_class(available_prof, class_missing, day) >= scheduler.MAX_DAILY_HOURS_FOR_TEACHER_FOR_CLASS:
                    continue
                # Is professor free at that slot?
                if scheduler.is_teacher_free_at(available_prof, day, hour):
                    if scheduler.get_teacher_hours_on_day(available_prof, day) < ImprovedSchoolScheduler.MAX_DAILY_HOURS_FOR_TEACHER:
                        scheduler.assign_slot(available_prof, class_missing, available_subject, day, hour)
                        if not scheduler.sanity_check_schedule():
                            return
                        break
                    else:
                        # Professor is free but has already max hours for that class on that day
                        print("swap_strategy_for_fully_booked")
                        swapped = swap_strategy_for_fully_booked(scheduler, available_prof, day)
                        if swapped:
                            scheduler.assign_slot(available_prof, class_missing, available_subject, day, hour)
                            if not scheduler.sanity_check_schedule():
                                return
                            break

                else:
                    # Professor is not free at that slot
                    print("swap_strategy_for_being_busy_on_slot")
                    swapped = swap_strategy_for_being_busy_on_slot(scheduler, available_prof, day, hour)
                    if swapped:
                        scheduler.assign_slot(available_prof, class_missing, available_subject, day, hour)
                        if not scheduler.sanity_check_schedule():
                            return
                        break

tryouts = 0
max_tryouts = 10
missing_classes = scheduler.missing_classes_on_schedule()
while missing_classes and tryouts < max_tryouts:
    print(f"Tryout {tryouts + 1} to insert missing classes via swap strategy...")
    insert_missing_classes_via_swap_strategy(scheduler=scheduler)
    missing_classes = scheduler.missing_classes_on_schedule()
    tryouts += 1
if not missing_classes:
    print("🆗 All missing classes have been successfully inserted into the schedule.")
else:
    print("❌ Some missing classes could not be inserted after maximum tryouts.")

scheduler.sanity_check_schedule()
scheduler.save_schedule('/Users/juan/Projects/oraccio/')

