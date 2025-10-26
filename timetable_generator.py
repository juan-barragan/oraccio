from ortools.sat.python import cp_model
import pandas as pd
import numpy as np

def create_timetable():
    # 1. Load and prepare data
    print("Loading data...")
    df = pd.read_csv('./data/docente_classes.csv')
    # Remove rows with NaN values and sort by number of hours (descending)
    df = df.dropna().sort_values('N.Ore', ascending=False)
    teachers = df['Identificativo'].unique()
    classes = df['Classi'].unique()
    subjects = df['Materia'].unique()
    
    print(f"Processing {len(teachers)} teachers and {len(classes)} classes...")
    print(f"Total teaching hours: {df['N.Ore'].sum()}")
    
    # Define time slots
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = list(range(8, 15))  # 8AM to 2PM
    
    # Create the model
    model = cp_model.CpModel()
    
    # 2. Create variables
    # assignments[(teacher, class_, day, hour)] = 1 if teacher teaches class at day,hour
    assignments = {}
    for _, row in df.iterrows():
        teacher = row['Identificativo']
        class_ = row['Classi']
        for day in days:
            for hour in hours:
                assignments[(teacher, class_, day, hour)] = model.NewBoolVar(
                    f'assign_{teacher}_{class_}_{day}_{hour}'
                )
    
    # 3. Add constraints
    
    # a) Each teacher-class combination must meet required hours per week
    for _, row in df.iterrows():
        teacher = row['Identificativo']
        class_ = row['Classi']
        required_hours = int(row['N.Ore'])  # Convert to int explicitly
        assignment_vars = []
        for day in days:
            for hour in hours:
                key = (teacher, class_, day, hour)
                if key in assignments:
                    assignment_vars.append(assignments[key])
        if assignment_vars:  # Only add constraint if we have variables
            model.Add(sum(assignment_vars) == required_hours)
    
    # b) No teacher can teach more than one class at the same time
    for teacher in teachers:
        for day in days:
            for hour in hours:
                relevant_classes = df[df['Identificativo'] == teacher]['Classi']
                model.Add(
                    sum(assignments.get((teacher, class_, day, hour), 0)
                        for class_ in relevant_classes) <= 1
                )
    
    # c) No class can have more than one teacher at the same time
    for class_ in classes:
        for day in days:
            for hour in hours:
                relevant_teachers = df[df['Classi'] == class_]['Identificativo']
                model.Add(
                    sum(assignments.get((teacher, class_, day, hour), 0)
                        for teacher in relevant_teachers) <= 1
                )
    
    # d) Maximum 6 hours per day per teacher (relaxed from 5)
    for teacher in teachers:
        for day in days:
            model.Add(
                sum(assignments.get((teacher, class_, day, hour), 0)
                    for class_ in df[df['Identificativo'] == teacher]['Classi']
                    for hour in hours) <= 6
            )
    
    # 4. Minimize gaps in schedule
    gaps = {}
    for teacher in teachers:
        for day in days:
            # Track first and last hour for each teacher per day
            first_hour = model.NewIntVar(0, len(hours)-1, f'first_{teacher}_{day}')
            last_hour = model.NewIntVar(0, len(hours)-1, f'last_{teacher}_{day}')
            
            # Calculate teaching hours for this teacher on this day
            hour_vars = []
            for hour_idx, hour in enumerate(hours):
                classes_at_hour = []
                for class_ in df[df['Identificativo'] == teacher]['Classi']:
                    key = (teacher, class_, day, hour)
                    if key in assignments:
                        classes_at_hour.append(assignments[key])
                
                if classes_at_hour:
                    # Create a bool variable that's true if teacher has any class this hour
                    has_class = model.NewBoolVar(f'has_class_{teacher}_{day}_{hour}')
                    model.Add(sum(classes_at_hour) >= 1).OnlyEnforceIf(has_class)
                    model.Add(sum(classes_at_hour) == 0).OnlyEnforceIf(has_class.Not())
                    
                    # Link first/last hour variables
                    model.Add(first_hour <= hour_idx).OnlyEnforceIf(has_class)
                    model.Add(last_hour >= hour_idx).OnlyEnforceIf(has_class)
                    hour_vars.append(has_class)
            
            # Calculate gap if teacher has any classes this day
            if hour_vars:
                gaps[(teacher, day)] = model.NewIntVar(0, len(hours), f'gap_{teacher}_{day}')
                # Gap is the difference between last and first hour minus the number of classes
                model.Add(gaps[(teacher, day)] >= last_hour - first_hour - sum(hour_vars) + 1)
    
    # Minimize total gaps
    model.Minimize(sum(gaps.values()))
    
    # 5. Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300  # Increase time limit to 5 minutes
    solver.parameters.num_search_workers = 8  # Use more CPU cores
    solver.parameters.log_search_progress = True  # Enable logging
    print("Solving model...")
    status = solver.Solve(model)
    
    # 6. Process the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Create schedule DataFrame for each day
        daily_schedules = {}
        for day in days:
            schedule = pd.DataFrame(index=teachers, columns=hours)
            for (teacher, class_, d, hour), var in assignments.items():
                if d == day and solver.Value(var):
                    schedule.at[teacher, hour] = class_
            daily_schedules[day] = schedule
        
        return daily_schedules
    else:
        return None

def save_timetable(daily_schedules, output_path='timetable.xlsx'):
    """Save the timetable to an Excel file with multiple sheets (one per day)."""
    if daily_schedules is None:
        print("No feasible solution found.")
        return
    
    with pd.ExcelWriter(output_path) as writer:
        for day, schedule in daily_schedules.items():
            schedule.to_excel(writer, sheet_name=day)
    print(f"Timetable saved to {output_path}")

if __name__ == "__main__":
    print("Generating timetable...")
    daily_schedules = create_timetable()
    save_timetable(daily_schedules)