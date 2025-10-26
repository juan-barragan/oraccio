import pandas as pd
import numpy as np
from collections import defaultdict

def load_data():
    """Load and prepare the input data."""
    df = pd.read_csv('./data/docente_classes.csv')
    return df.dropna().sort_values('N.Ore', ascending=False)

def create_timetable():
    print("Loading data...")
    # Load and prepare data
    df = load_data()
    
    # Initialize schedule
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = list(range(8, 15))  # 8AM to 3PM (including 14:00)
    best_schedule = None
    best_allocated = 0
    best_remaining = None
    used_hours = list(range(8, 15))
    
    def is_slot_available(schedule, teacher, class_, day, hour, relax_constraints=False):
        # Core constraints that can't be relaxed
        if any(teacher == t for t in schedule[day][hour].values()):
            return False if relax_constraints else (False, float('-inf'))
        if class_ in schedule[day][hour]:
            return False if relax_constraints else (False, float('-inf'))
            
        # Check teacher's daily hours - can be slightly relaxed
        teacher_hours = sum(1 for h in used_hours if any(teacher == t for t in schedule[day][h].values()))
        max_daily_hours = 7 if relax_constraints else 6
        if teacher_hours >= max_daily_hours:
            return False if relax_constraints else (False, float('-inf'))
            
        # Special time constraints - can be relaxed for some slots
        ALLOWED_14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']
        score = 0
        
        if hour == 14:  # For the 14:00 hour slot
            if day == 'LUN' or day == 'MER':
                if class_ not in ALLOWED_14:
                    if not relax_constraints:
                        return False if relax_constraints else (False, float('-inf'))
                    score -= 50
                else:
                    score += 20
            elif day == 'VEN':
                if class_ != '3L':
                    if not relax_constraints:
                        return False if relax_constraints else (False, float('-inf'))
                    score -= 100
                else:
                    score += 40
                    
        # Scoring factors
        # Prefer early hours except for special cases
        if class_ in ALLOWED_14 and hour == 14:
            score += 30
        else:
            score += (15 - hour) * 5
            
        # Prefer keeping similar classes together
        class_prefix = class_[0]
        neighbors = []
        for existing_class in schedule[day][hour].keys():
            if existing_class[0] == class_prefix:
                score += 10
                
        return True if relax_constraints else (True, score)

    def evaluate_swap_impact(schedule, day1, hour1, class1, teacher1, day2, hour2, class2, teacher2):
        score = 0
        
        # Check consecutive hours for both teachers
        def count_consecutive(day, hour, teacher):
            count = 0
            for h in range(hour-1, 7, -1):  # Check backwards
                if any(teacher == t for t in schedule[day][h].values()):
                    count += 1
                else:
                    break
            for h in range(hour+1, 15):  # Check forwards
                if any(teacher == t for t in schedule[day][h].values()):
                    count += 1
                else:
                    break
            return count
        
        # Score current arrangement
        before_score = 0
        before_score -= abs(count_consecutive(day1, hour1, teacher1) - 3) * 10
        before_score -= abs(count_consecutive(day2, hour2, teacher2) - 3) * 10
        
        # Simulate swap
        schedule[day1][hour1][class1] = teacher2
        schedule[day2][hour2][class2] = teacher1
        
        # Score new arrangement
        after_score = 0
        after_score -= abs(count_consecutive(day1, hour1, teacher2) - 3) * 10
        after_score -= abs(count_consecutive(day2, hour2, teacher1) - 3) * 10
        
        # Restore original state
        schedule[day1][hour1][class1] = teacher1
        schedule[day2][hour2][class2] = teacher2
        
        # Calculate improvement
        score = after_score - before_score
        
        # Special time slot considerations
        if hour1 == 14 or hour2 == 14:
            ALLOWED_14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']
            if (hour1 == 14 and class2 in ALLOWED_14) or (hour2 == 14 and class1 in ALLOWED_14):
                score += 50
            
        # Prefer keeping classes with same year level together
        def get_year(class_):
            return class_[0] if class_[0].isdigit() else -1
            
        year1, year2 = get_year(class1), get_year(class2)
        if year1 == year2:
            score += 20
            
        return score

    def try_swap(schedule, day1, hour1, class1, day2, hour2, class2):
        # Skip invalid swaps or self-swaps
        if (day1, hour1) == (day2, hour2) or class1 == class2:
            return False
            
        try:
            # Get teachers for both slots
            teacher1 = schedule[day1][hour1].get(class1)
            teacher2 = schedule[day2][hour2].get(class2)
            
            if not teacher1 or not teacher2:
                return False
                
            # Safety check - ensure classes exist in schedule
            if class1 not in schedule[day1][hour1] or class2 not in schedule[day2][hour2]:
                return False
                
            # Create backup of the slots
            backup1 = schedule[day1][hour1].copy()
            backup2 = schedule[day2][hour2].copy()
            
            # Evaluate impact before making changes
            impact_score = evaluate_swap_impact(schedule, day1, hour1, class1, teacher1, 
                                             day2, hour2, class2, teacher2)
            
            # Only proceed with beneficial or neutral swaps
            if impact_score < 0:
                return False
            
            # Temporarily remove both assignments
            del schedule[day1][hour1][class1]
            del schedule[day2][hour2][class2]
            
            # Check if swap is valid with original constraints
            valid1 = is_slot_available(schedule, teacher1, class2, day2, hour2)
            valid2 = is_slot_available(schedule, teacher2, class1, day1, hour1)
            
            if isinstance(valid1, tuple): valid1 = valid1[0]
            if isinstance(valid2, tuple): valid2 = valid2[0]
            
            if not (valid1 and valid2):
                # Try with relaxed constraints
                if not (is_slot_available(schedule, teacher1, class2, day2, hour2, True) and 
                       is_slot_available(schedule, teacher2, class1, day1, hour1, True)):
                    # If still not valid, restore and return False
                    schedule[day1][hour1] = backup1
                    schedule[day2][hour2] = backup2
                    return False
            
            # Perform the swap
            schedule[day1][hour1][class1] = teacher2
            schedule[day2][hour2][class2] = teacher1
            return True
            
        except Exception:
            # If anything goes wrong, restore from backup and return False
            if 'backup1' in locals() and 'backup2' in locals():
                schedule[day1][hour1] = backup1
                schedule[day2][hour2] = backup2
            return False

    def try_allocation(shuffle_days=True, shuffle_hours=True, prioritize_difficult=True):
        schedule = {day: {h: {} for h in range(8, 15)} for day in days}
        remaining = {}
        for _, row in df.iterrows():
            remaining[(row['Identificativo'], row['Classi'])] = int(row['N.Ore'])
        
        # Sort assignments by comprehensive difficulty
        assignments = [(teacher, class_, hours) for (teacher, class_), hours in remaining.items()]
        if prioritize_difficult:
            def get_assignment_score(teacher, class_, hours):
                # Base difficulty from hours needed
                score = hours * 10
                
                # Add score for special time constraints
                if class_ == '3L':
                    score += 50  # Highest priority - has VEN14 constraint
                elif class_ in ['3E', '4E', '5E', '1L', '1I', '2L', '2I']:
                    score += 30  # High priority - has LUN14/MER14 constraints
                
                # Add score based on teacher's total hours
                teacher_total_hours = sum(h for (t, _), h in remaining.items() if t == teacher)
                score += teacher_total_hours * 5
                
                # Add score for classes that appear frequently
                class_frequency = sum(1 for (_, c), _ in remaining.items() if c == class_)
                score += class_frequency * 15
                
                return score
            
            assignments.sort(key=lambda x: get_assignment_score(x[0], x[1], x[2]), reverse=True)
        
        # Create day and hour sequences with optional shuffling
        day_seq = days.copy()
        hour_seq = hours.copy()
        if shuffle_days:
            import random
            random.shuffle(day_seq)
        if shuffle_hours:
            import random
            random.shuffle(hour_seq)
        
        total_allocated = 0
        for teacher, class_, hours_needed in assignments:
            hours_left = hours_needed
            while hours_left > 0:
                allocated = False
                best_slot = None
                best_score = float('-inf')
                best_day = None
                
                # Find best available slot
                for day in day_seq:
                    for hour in hour_seq:
                        slot_result = is_slot_available(schedule, teacher, class_, day, hour)
                        if isinstance(slot_result, tuple):
                            available, score = slot_result
                            if available and score > best_score:
                                best_score = score
                                best_slot = hour
                                best_day = day
                
                if best_slot is not None and best_day is not None:
                    schedule[best_day][best_slot][class_] = teacher
                    hours_left -= 1
                    total_allocated += 1
                    allocated = True
                
                if not allocated:
                    # Try relaxed constraints
                    for day in day_seq:
                        if allocated:
                            break
                        for hour in hour_seq:
                            if is_slot_available(schedule, teacher, class_, day, hour, True):
                                schedule[day][hour][class_] = teacher
                                hours_left -= 1
                                total_allocated += 1
                                allocated = True
                                break
                
                if not allocated:
                    # Try backtracking with swaps
                    swap_found = False
                    for d1 in days:
                        if swap_found:
                            break
                        for h1 in range(8, 15):
                            if swap_found:
                                break
                            for d2 in days:
                                for h2 in range(8, 15):
                                    items1 = list(schedule[d1][h1].items())
                                    items2 = list(schedule[d2][h2].items())
                                    for c1, _ in items1:
                                        for c2, _ in items2:
                                            if try_swap(schedule, d1, h1, c1, d2, h2, c2):
                                                if is_slot_available(schedule, teacher, class_, d1, h1, True):
                                                    schedule[d1][h1][class_] = teacher
                                                    hours_left -= 1
                                                    total_allocated += 1
                                                    allocated = True
                                                    swap_found = True
                                                    break
                                        if swap_found:
                                            break
                
                if not allocated:
                    remaining[(teacher, class_)] = hours_left
                    break
        
        # Final optimization pass
        max_iterations = 10
        iteration = 0
        improved = True
        while improved and iteration < max_iterations:
            iteration += 1
            improved = False
            for d1 in days:
                for h1 in range(8, 15):
                    if not schedule[d1][h1]:
                        continue
                    for d2 in days:
                        for h2 in range(8, 15):
                            if not schedule[d2][h2]:
                                continue
                            items1 = list(schedule[d1][h1].items())
                            items2 = list(schedule[d2][h2].items())
                            for c1, _ in items1:
                                for c2, _ in items2:
                                    if try_swap(schedule, d1, h1, c1, d2, h2, c2):
                                        improved = True
                                        break
                                if improved:
                                    break
                            if improved:
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
        
        return schedule, total_allocated, remaining
    
    # Try multiple times with different strategies
    print(f"Processing {len(df['Identificativo'].unique())} teachers and {len(df['Classi'].unique())} classes...")
    print(f"Total teaching hours to allocate: {sum(int(row['N.Ore']) for _, row in df.iterrows())}")
    
    # Try different combinations of strategies
    strategies = [
        (True, True, True),    # Shuffle both, prioritize difficult
        (False, True, True),   # Only shuffle hours, prioritize difficult
        (True, False, True),   # Only shuffle days, prioritize difficult
        (False, False, True),  # No shuffle, prioritize difficult
        (True, True, False),   # Shuffle both, no prioritization
    ]
    
    for shuffle_days, shuffle_hours, prioritize in strategies:
        schedule, allocated, remaining = try_allocation(shuffle_days, shuffle_hours, prioritize)
        if allocated > best_allocated:
            best_allocated = allocated
            best_schedule = schedule
            best_remaining = remaining
            if allocated == sum(int(row['N.Ore']) for _, row in df.iterrows()):
                break  # Perfect solution found
    
    print(f"Allocated {best_allocated} hours out of {sum(int(row['N.Ore']) for _, row in df.iterrows())} total hours")
    
    if best_remaining:
        # Print details about unallocated hours
        unallocated = [(t, c, h) for (t, c), h in best_remaining.items() if h > 0]
        if unallocated:
            print("\nUnallocated hours:")
            for teacher, class_, hours in unallocated:
                print(f"  {teacher} - {class_}: {hours} hours remaining")
    
    # Convert to a single DataFrame with day-hour columns
    teachers = sorted(df['Identificativo'].unique())
    schedule_data = []
    
    for teacher in teachers:
        row = {'Teacher': teacher}
        for day in days:
            for hour in used_hours:
                col = f"{day}{hour}"
                # Find what class (if any) this teacher has at this time
                if best_schedule is not None:
                    classes = [c for c, t in best_schedule[day][hour].items() if t == teacher]
                    row[col] = classes[0] if classes else ''
                else:
                    row[col] = ''
        schedule_data.append(row)
    
    # Create final DataFrame
    result = pd.DataFrame(schedule_data)
    result.set_index('Teacher', inplace=True)
    
    # Sort columns to ensure correct order
    cols = [f"{day}{hour}" for day in days for hour in used_hours]
    result = result.reindex(columns=cols)
    
    return result

if __name__ == "__main__":
    print("Generating timetable...")
    schedule = create_timetable()
    if schedule is not None:
        schedule.to_csv('generated_schedule_optimized.csv')
        print("Timetable saved to generated_schedule_optimized.csv")