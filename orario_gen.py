# %%
import pandas as pd

df = pd.read_csv('./data/docente_classes.csv')
teachers = df['Identificativo'].dropna().unique()
days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
hours = [8, 9, 10, 11, 12, 13, 14]
slots = [f'{d}{h}' for d in days for h in hours]
schedule = pd.DataFrame('', index=teachers, columns=slots)

def count_holes(day_slots):
    filled = [i for i, v in enumerate(day_slots) if v != '']
    if len(filled) <= 1:
        return 0
    holes = 0
    for i in range(filled[0], filled[-1]):
        if i not in filled:
            holes += 1
    return holes

def weekly_holes(teacher_row):
    total = 0
    for day in days:
        day_slots = [teacher_row[f'{day}{h}'] for h in hours]
        total += count_holes(day_slots)
    return total

for _, row in df.iterrows():
    teacher = row['Identificativo']
    class_ = row['Classi']
    n_ore = row['N.Ore']
    if pd.isnull(teacher) or pd.isnull(class_) or pd.isnull(n_ore):
        continue
    n_ore = int(n_ore)
    assigned = 0
    for day in days:
        # Get current hours for this teacher on this day
        day_slots = [f'{day}{h}' for h in hours]
        current_hours = sum(1 for slot in day_slots if schedule.loc[teacher, slot] != '')
        if current_hours >= 5:
            continue
        for slot in day_slots:
            if schedule.loc[teacher, slot] == '' and assigned < n_ore and current_hours < 5:
                # Tentatively assign
                schedule.loc[teacher, slot] = class_
                # Check constraints
                day_vals = [schedule.loc[teacher, s] for s in day_slots]
                if not (sum(1 for v in day_vals if v != '') <= 5 and count_holes(day_vals) <= 2 and weekly_holes(schedule.loc[teacher]) <= 3):
                    # Undo if constraints violated
                    schedule.loc[teacher, slot] = ''
                else:
                    assigned += 1
                    current_hours += 1
            if assigned == n_ore:
                break
        if assigned == n_ore:
            break

schedule.to_csv('generated_schedule_constrained.csv')

# %%
schedule

# %%



