from collections import namedtuple
import pandas as pd

classe = namedtuple('classe', ['teacher', 'day_hour'])

def check_column_(df, column_name, total_number):
    x = df[column_name]
    x = x[~pd.isnull(x)]
    return len(x) == total_number & len(set(x)) == total_number

def duplicated_indices_in_column(df, column_name):
    x = df[column_name]
    duplicated_indices = x[~pd.isnull(x)].index[x[~pd.isnull(x)].duplicated(keep=False)]
    return duplicated_indices.values

def holes_by_day(df, teacher):
    """
    Returns a dictionary {day: number_of_holes} for the given teacher.
    Assumes columns are like 'LUN8', 'LUN9', ..., 'VEN14'.
    A hole is a gap (empty slot) between two non-empty slots in the same day.
    """
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = [8, 9, 10, 11, 12, 13, 14]
    holes = {}
    for day in days:
        # Get the values for the teacher for this day, in hour order
        vals = [df.loc[teacher, f"{day}{hour}"] if f"{day}{hour}" in df.columns else None for hour in hours]
        # Find indices of non-empty slots
        non_empty = [i for i, v in enumerate(vals) if pd.notnull(v) and v != '']
        if len(non_empty) <= 1:
            holes[day] = 0
            continue
        # Count the number of empty slots between first and last non-empty
        first, last = non_empty[0], non_empty[-1]
        n_holes = 0
        for i in range(first, last):
            if i not in non_empty:
                n_holes += 1
        holes[day] = n_holes
    return holes

def swap(df, classe_1, classe_2):
    classroom_temp = df.loc[classe_1.teacher, classe_1.day_hour] 
    df.loc[classe_1.teacher, classe_1.day_hour] = df.loc[classe_2.teacher, classe_2.day_hour]
    df.loc[classe_2.teacher, classe_2.day_hour] = classroom_temp

def allowed_permutation(df, classe_1, classe_2, not_allowed):
    classroom_1 = df.loc[classe_1.teacher, classe_1.day_hour]
    classroom_2 = df.loc[classe_2.teacher, classe_2.day_hour]    
    classroom_1_allowed = classroom_1 not in not_allowed.get(classe_2.day_hour, set())
    classroom_2_allowed = classroom_2 not in not_allowed.get(classe_1.day_hour, set())
    if not classroom_1_allowed or not classroom_2_allowed:
        return False
    
    temp_df = df.copy()
    swap(temp_df, classe_1, classe_2)
    for professor in df.index:
        holes = holes_by_day(temp_df, professor)
        for k in holes:
            if holes[k] > 2:
                return False
    return True

def permute(df, classe_1, classe_2):
    classroom_temp = df.loc[classe_1.teacher, classe_1.day_hour] 
    df.loc[classe_1.teacher, classe_1.day_hour] = df.loc[classe_2.teacher, classe_2.day_hour]
    df.loc[classe_2.teacher, classe_2.day_hour] = classroom_temp
    # Check if there are duplicates
    first_column_name = classe_1.day_hour
    second_column_name = classe_2.day_hour
    first_column_duplicated_indices = duplicated_indices_in_column(df, first_column_name)
    second_column_duplicated_indices = duplicated_indices_in_column(df, second_column_name)
    return (first_column_duplicated_indices, first_column_name), (second_column_duplicated_indices, second_column_name)

def find_next_available_slot(df, teacher, seen):
    for col in df.columns:
        if classe(teacher, col) in seen:
            continue
        val = df.loc[teacher, col]
        if val=='' or pd.isnull(val):
            return col
    return None

def find_all_available_slots(df, teacher):
    answer = []
    for col in df.columns:
        val = df.loc[teacher, col]
        if val=='' or pd.isnull(val):
            answer.append(col)
    return answer

# Quality function: contiguous holes (2 or more consecutive empty slots between lessons) get weight 2, normal holes weight 1
def schedule_quality(df):
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = [8, 9, 10, 11, 12, 13, 14]
    total_score = 0
    for teacher in df.index:
        for day in days:
            vals = [df.loc[teacher, f"{day}{hour}"] if f"{day}{hour}" in df.columns else None for hour in hours]
            # Find indices of non-empty slots
            non_empty = [i for i, v in enumerate(vals) if pd.notnull(v) and v != '']
            if len(non_empty) <= 1:
                continue
            first, last = non_empty[0], non_empty[-1]
            i = first
            while i < last:
                if i not in non_empty:
                    # Start of a hole
                    hole_len = 1
                    j = i + 1
                    while j < last and j not in non_empty:
                        hole_len += 1
                        j += 1
                    if hole_len > 1:
                        total_score += 2 * hole_len  # contiguous hole
                    else:
                        total_score += 1  # single hole
                    i = j
                else:
                    i += 1
    return total_score