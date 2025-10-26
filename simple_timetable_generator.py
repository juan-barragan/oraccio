import pandas as pd
import numpy as np
from collections import defaultdict

def create_timetable():
    # 1. Load and prepare data
    df = pd.read_csv('./data/docente_classes.csv')
    teachers = df['Identificativo'].unique()
    classes = df['Classi'].unique()
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = list(range(8,15))  # 6 hours per day
    
    # Create empty schedule
    schedule = {day: pd.DataFrame(index=hours, columns=classes) for day in days}
    
    # Create a dictionary to track remaining hours for each teacher-class combination
    remaining_hours = {}
    for _, row in df.iterrows():
        remaining_hours[(row['Identificativo'], row['Classi'])] = row['N.Ore']
    
    # Create a dictionary to track teacher's daily hours
    teacher_daily_hours = {(teacher, day): 0 for teacher in teachers for day in days}
    
    # 2. Fill the schedule
    for day in days:
        for hour in hours:
            # Sort teacher-class pairs by remaining hours (prioritize those with more hours)
            pairs = [(t, c) for (t, c), h in remaining_hours.items() if h > 0]
            pairs.sort(key=lambda x: remaining_hours[x], reverse=True)
            
            for teacher, class_ in pairs:
                # Check if this slot is available
                if pd.isnull(schedule[day].at[hour, class_]) and teacher_daily_hours[(teacher, day)] < 5:
                    # Check if teacher is not already teaching another class at this time
                    teacher_busy = False
                    for c in classes:
                        if schedule[day].at[hour, c] == teacher:
                            teacher_busy = True
                            break
                    
                    if not teacher_busy:
                        # Assign the teacher to this slot
                        schedule[day].at[hour, class_] = teacher
                        remaining_hours[(teacher, class_)] -= 1
                        teacher_daily_hours[(teacher, day)] += 1
    
    # Check if all hours were allocated
    unallocated = [(t, c, h) for (t, c), h in remaining_hours.items() if h > 0]
    if unallocated:
        print("Warning: Could not allocate all hours:")
        for teacher, class_, hours in unallocated:
            print(f"  {teacher} - {class_}: {hours} hours remaining")
    
    return schedule

def save_timetable(schedule, output_path='timetable.xlsx'):
    """Save the timetable to an Excel file with multiple sheets (one per day)."""
    with pd.ExcelWriter(output_path) as writer:
        for day, day_schedule in schedule.items():
            day_schedule.to_excel(writer, sheet_name=day)
    print(f"Timetable saved to {output_path}")

if __name__ == "__main__":
    print("Generating timetable...")
    schedule = create_timetable()
    save_timetable(schedule)
    print("Done!")