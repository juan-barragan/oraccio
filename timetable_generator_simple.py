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
            return False
        if class_ in schedule[day][hour]:
            return False
            
        # Check teacher's daily hours - can be slightly relaxed
        teacher_hours = sum(1 for h in used_hours if any(teacher == t for t in schedule[day][h].values()))
        max_daily_hours = 7 if relax_constraints else 6
        if teacher_hours >= max_daily_hours:
            return False
            
        # Special time constraints - can be relaxed for some slots
        ALLOWED_14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']
        if hour == 14:  # For the 14:00 hour slot
            if day == 'LUN' or day == 'MER':
                if class_ not in ALLOWED_14 and not relax_constraints:
                    return False
            elif day == 'VEN':
                if class_ != '3L' and not relax_constraints:
                    return False
                
        # Calculate slot preference score (higher is better)
        score = 0
        if hour == 14:
            if class_ in ALLOWED_14:
                score += 10
            if day == 'VEN' and class_ == '3L':
                score += 20
                
        # Early hours are generally preferred
        score += (15 - hour) * 2
        
        return True if relax_constraints else (True, score)
    
    def evaluate_swap_impact(schedule, day1, hour1, class1, teacher1, day2, hour2, class2, teacher2):
        score = 0
        
        # Check consecutive hours for both teachers before and after swap
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
        
        # Current consecutive counts
        consec1_before = count_consecutive(day1, hour1, teacher1)
        consec2_before = count_consecutive(day2, hour2, teacher2)
        
        # Simulate swap
        tmp1, tmp2 = teacher1, teacher2
        schedule[day1][hour1][class1] = tmp2
        schedule[day2][hour2][class2] = tmp1
        
        # New consecutive counts
        consec1_after = count_consecutive(day1, hour1, teacher2)
        consec2_after = count_consecutive(day2, hour2, teacher1)
        
        # Restore original state
        schedule[day1][hour1][class1] = teacher1
        schedule[day2][hour2][class2] = teacher2
        
        # Scoring (higher is better)
        score += (consec1_after + consec2_after) - (consec1_before + consec2_before) * 10
        
        # Prefer swaps that keep special time slot constraints
        if hour1 == 14 or hour2 == 14:
            ALLOWED_14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']
            if (hour1 == 14 and class2 in ALLOWED_14) or (hour2 == 14 and class1 in ALLOWED_14):
                score += 50
                
        # Prefer swaps that don't break up teacher's existing patterns
        score -= abs(hour1 - hour2) * 5  # Penalize moving classes far apart
        
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
                
            # Evaluate impact score
            impact_score = evaluate_swap_impact(schedule, day1, hour1, class1, teacher1, 
                                             day2, hour2, class2, teacher2)
            
            # Only proceed with beneficial swaps
            if impact_score <= 0:
                return False
                
            # Create backup of the slots
            backup1 = schedule[day1][hour1].copy()
            backup2 = schedule[day2][hour2].copy()
            
            # Temporarily remove both assignments
            del schedule[day1][hour1][class1]
            del schedule[day2][hour2][class2]
            
            return True
        except Exception:
            # If anything goes wrong, return False
            return False
        
        try:
            # Check if swap is valid
            valid = (is_slot_available(schedule, teacher1, class2, day2, hour2) and 
                    is_slot_available(schedule, teacher2, class1, day1, hour1))
            
            if valid:
                # Perform the swap
                schedule[day1][hour1][class1] = teacher2
                schedule[day2][hour2][class2] = teacher1
                return True
            
            # If not valid, restore from backup
            schedule[day1][hour1] = backup1
            schedule[day2][hour2] = backup2
            return False
            
        except Exception:
            # If anything goes wrong, restore from backup and return False
            schedule[day1][hour1] = backup1
            schedule[day2][hour2] = backup2
            return False

    def try_allocation(shuffle_days=True, shuffle_hours=True, prioritize_difficult=True):
        schedule = {day: {h: {} for h in range(8, 15)} for day in days}
        remaining = {}
        for _, row in df.iterrows():
            remaining[(row['Identificativo'], row['Classi'])] = int(row['N.Ore'])
        
        # Sort assignments by difficulty
        assignments = [(teacher, class_, hours) for (teacher, class_), hours in remaining.items()]
        if prioritize_difficult:
            # Sort by hours and number of constraints
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
                score += teacher_total_hours * 5  # Teachers with more hours are harder to schedule
                
                # Add score for classes that appear frequently
                class_frequency = sum(1 for (_, c), _ in remaining.items() if c == class_)
                score += class_frequency * 15  # Classes with many teachers are harder to schedule
                
                return score
            
            # Sort by comprehensive difficulty score
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
        # First pass: Try to allocate all hours
        for teacher, class_, hours_needed in assignments:
            hours_left = hours_needed
            while hours_left > 0:
                allocated = False
                for day in day_seq:
                    if allocated:
                        break
                    # Try normal allocation first
                    best_slot = None
                    best_score = float('-inf')
                    for hour in range(8, 15):
                        slot_available = is_slot_available(schedule, teacher, class_, day, hour)
                        if isinstance(slot_available, tuple):
                            available, score = slot_available
                            if available and score > best_score:
                                best_score = score
                                best_slot = hour
                    
                    if best_slot is not None:
                        schedule[day][best_slot][class_] = teacher
                        hours_left -= 1
                        total_allocated += 1
                        allocated = True
                        break
                    
                    # If normal allocation fails, try with relaxed constraints
                    if not allocated:
                        for hour in range(8, 15):
                            if is_slot_available(schedule, teacher, class_, day, hour, relax_constraints=True):
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
                                                                        # Find classes that could be swapped
                                    items1 = list(schedule[d1][h1].items())
                                    items2 = list(schedule[d2][h2].items())
                                    for c1, t1 in items1:
                                        for c2, t2 in items2:
                                            if (d1, h1) != (d2, h2):  # Don't swap same slot
                                                if try_swap(schedule, d1, h1, c1, d2, h2, c2):
                                                    # After swap, try to allocate in the freed slot
                                                    if is_slot_available(schedule, teacher, class_, d1, h1):
                                                        schedule[d1][h1][class_] = teacher
                                                        hours_left -= 1
                                                        total_allocated += 1
                                                        allocated = True
                                                        swap_found = True
                                                        break
                                        if swap_found:
                                            break
                    
                    if not allocated:
                        # If still not allocated after trying swaps
                        remaining[(teacher, class_)] = hours_left
                        break  # Move to next assignment
        
        # Final optimization pass - try to reduce fragmentation
        max_iterations = 10  # Limit optimization attempts
        iteration = 0
        improved = True
        while improved and iteration < max_iterations:
            iteration += 1
            improved = False
            for d1 in days:
                for h1 in range(8, 15):
                    if not schedule[d1][h1]:  # Skip empty slots
                        continue
                    for d2 in days:
                        for h2 in range(8, 15):
                            if not schedule[d2][h2]:  # Skip empty slots
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
                classes = [c for c, t in schedule[day][hour].items() if t == teacher]
                row[col] = classes[0] if classes else ''
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
        schedule.to_csv('generated_schedule.csv')
        print("Timetable saved to generated_schedule.csv")