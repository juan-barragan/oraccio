import pandas as pd
import numpy as np
from collections import defaultdict
import random

class ProfessorScheduler:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.days = ['MON', 'MAR', 'MER', 'GIO', 'VEN']  # Monday to Friday
        self.hours = list(range(8, 15))  # 8AM to 2PM (14:00)

        # Time constraints for 14:00 slots
        self.ALLOWED_14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']

        # Load and prepare data
        self.load_data()

    def load_data(self):
        """Load and prepare the professor-class data."""
        df = pd.read_csv(self.csv_file_path)
        df = df.dropna()

        # Group by professor and class to get total hours needed
        self.assignments = defaultdict(dict)
        for _, row in df.iterrows():
            professor = row['Identificativo']
            class_name = row['Classi']
            hours = int(row['N.Ore'])
            self.assignments[professor][class_name] = hours

        self.professors = list(self.assignments.keys())
        self.classes = set()
        for prof_assignments in self.assignments.values():
            self.classes.update(prof_assignments.keys())
        self.classes = sorted(list(self.classes))

    def is_slot_available(self, schedule, professor, class_name, day, hour):
        """Check if a slot is available for a professor-class assignment."""
        # Check if professor is already teaching at this time
        if any(professor == p for p in schedule[day][hour].values()):
            return False

        # Check if class already has a teacher at this time
        if class_name in schedule[day][hour]:
            return False

        # Check professor's daily hour limit (max 6 hours per day)
        professor_hours_today = sum(1 for h in self.hours
                                  if any(professor == p for p in schedule[day][h].values()))
        if professor_hours_today >= 6:
            return False

        # Special time constraints for 14:00 slots
        if hour == 14:
            if day in ['MON', 'MER']:  # Monday and Wednesday
                if class_name not in self.ALLOWED_14:
                    return False
            elif day == 'VEN':  # Friday
                if class_name != '3L':
                    return False

        return True

    def calculate_assignment_priority(self, professor, class_name, hours_needed):
        """Calculate priority score for an assignment (higher = more urgent)."""
        score = 0

        # Base score from hours needed
        score += hours_needed * 10

        # Higher priority for classes with special time constraints
        if class_name == '3L':
            score += 50  # Highest priority - only allowed on VEN14
        elif class_name in self.ALLOWED_14:
            score += 30  # High priority - has LUN14/MER14 constraints

        # Consider professor's total workload
        total_professor_hours = sum(self.assignments[professor].values())
        score += total_professor_hours * 2

        # Consider class frequency (classes taught by many professors are harder)
        class_frequency = sum(1 for prof in self.professors
                            if class_name in self.assignments[prof])
        score += class_frequency * 5

        return score

    def find_best_slot(self, schedule, professor, class_name, day_order, hour_order):
        """Find the best available slot for an assignment."""
        best_score = -1
        best_slot = None

        for day in day_order:
            for hour in hour_order:
                if self.is_slot_available(schedule, professor, class_name, day, hour):
                    # Calculate slot preference score
                    score = 0

                    # Prefer early hours
                    score += (15 - hour) * 2

                    # Prefer slots that maintain consecutive teaching
                    consecutive_before = 0
                    consecutive_after = 0

                    # Check consecutive hours before
                    for h in range(hour - 1, 7, -1):
                        if any(professor == p for p in schedule[day][h].values()):
                            consecutive_before += 1
                        else:
                            break

                    # Check consecutive hours after
                    for h in range(hour + 1, 15):
                        if any(professor == p for p in schedule[day][h].values()):
                            consecutive_after += 1
                        else:
                            break

                    # Prefer slots that create or maintain consecutive blocks
                    total_consecutive = consecutive_before + consecutive_after + 1
                    if total_consecutive >= 3:
                        score += 20
                    elif total_consecutive >= 2:
                        score += 10

                    # Special bonus for 14:00 slots that are allowed
                    if hour == 14 and class_name in self.ALLOWED_14:
                        score += 15

                    if score > best_score:
                        best_score = score
                        best_slot = (day, hour)

        return best_slot

    def create_schedule(self):
        """Create the professor schedule using an optimized algorithm."""
        print("Creating professor schedule...")

        # Initialize empty schedule
        schedule = {day: {hour: {} for hour in self.hours} for day in self.days}

        # Track remaining hours for each professor-class combination
        remaining_hours = defaultdict(lambda: defaultdict(int))
        for professor, classes in self.assignments.items():
            for class_name, hours in classes.items():
                remaining_hours[professor][class_name] = hours

        # Convert to list of assignments sorted by priority
        assignments = []
        for professor, classes in remaining_hours.items():
            for class_name, hours in classes.items():
                priority = self.calculate_assignment_priority(professor, class_name, hours)
                assignments.append((priority, professor, class_name, hours))

        assignments.sort(reverse=True)  # Highest priority first

        total_allocated = 0
        total_required = sum(sum(classes.values()) for classes in self.assignments.values())

        print(f"Total hours to allocate: {total_required}")

        # Multi-pass allocation with different strategies
        strategies = [
            {'shuffle_days': False, 'shuffle_hours': False, 'name': 'Priority Order'},
            {'shuffle_days': True, 'shuffle_hours': False, 'name': 'Shuffle Days'},
            {'shuffle_days': False, 'shuffle_hours': True, 'name': 'Shuffle Hours'},
        ]

        best_schedule = None
        best_allocated = 0

        for strategy in strategies:
            print(f"\nTrying strategy: {strategy['name']}")

            # Create day and hour orderings
            day_order = self.days.copy()
            hour_order = self.hours.copy()

            if strategy['shuffle_days']:
                random.shuffle(day_order)
            if strategy['shuffle_hours']:
                random.shuffle(hour_order)

            current_schedule = {day: {hour: {} for hour in self.hours} for day in self.days}
            current_allocated = 0

            # Reset remaining hours for this strategy
            current_remaining = defaultdict(lambda: defaultdict(int))
            for professor, classes in remaining_hours.items():
                for class_name, hours in classes.items():
                    current_remaining[professor][class_name] = hours

            # Allocate assignments
            for _, professor, class_name, _ in assignments:
                hours_needed = current_remaining[professor][class_name]

                while hours_needed > 0 and current_remaining[professor][class_name] > 0:
                    # Find best available slot
                    slot = self.find_best_slot(current_schedule, professor, class_name, day_order, hour_order)

                    if slot:
                        day, hour = slot
                        current_schedule[day][hour][class_name] = professor
                        hours_needed -= 1
                        current_remaining[professor][class_name] -= 1
                        current_allocated += 1
                    else:
                        # No slot found, move to next assignment
                        break

            print(f"Strategy '{strategy['name']}': {current_allocated}/{total_required} hours allocated")

            if current_allocated > best_allocated:
                best_allocated = current_allocated
                best_schedule = current_schedule

        print(f"\nBest result: {best_allocated}/{total_required} hours allocated ({best_allocated/total_required*100:.1f}%)")

        # Report unallocated hours
        unallocated = []
        for professor, classes in remaining_hours.items():
            for class_name, hours in classes.items():
                if hours > 0:
                    unallocated.append((professor, class_name, hours))

        if unallocated:
            print("\nUnallocated hours:")
            for professor, class_name, hours in sorted(unallocated):
                print(f"  {professor} - {class_name}: {hours} hours")

        return best_schedule, best_allocated, total_required

    def schedule_to_dataframe(self, schedule):
        """Convert schedule to DataFrame format."""
        # Create columns for each day-hour combination
        columns = []
        for day in self.days:
            for hour in self.hours:
                columns.append(f"{day}{hour}")

        # Create data for each professor
        data = []
        for professor in self.professors:
            row = {'Professor': professor}
            for day in self.days:
                for hour in self.hours:
                    col = f"{day}{hour}"
                    # Find which class this professor teaches at this time
                    classes = [class_name for class_name, prof in schedule[day][hour].items()
                             if prof == professor]
                    row[col] = classes[0] if classes else ''
            data.append(row)

        df = pd.DataFrame(data)
        df.set_index('Professor', inplace=True)
        return df

def main():
    # Create scheduler
    scheduler = ProfessorScheduler('/Users/juan/Projects/oraccio/data/docente_classes.csv')

    # Generate schedule
    schedule, allocated, total = scheduler.create_schedule()

    # Convert to DataFrame and save
    if schedule:
        df_schedule = scheduler.schedule_to_dataframe(schedule)
        output_file = '/Users/juan/Projects/oraccio/professor_schedule.csv'
        df_schedule.to_csv(output_file)
        print(f"\nSchedule saved to: {output_file}")

        # Print summary
        print(f"\nSchedule Summary:")
        print(f"Professors: {len(scheduler.professors)}")
        print(f"Classes: {len(scheduler.classes)}")
        print(f"Hours allocated: {allocated}/{total} ({allocated/total*100:.1f}%)")

if __name__ == "__main__":
    main()