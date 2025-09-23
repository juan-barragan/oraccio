import pandas as pd
import numpy as np
from dataframe import logic
from tools import file, curricula


def find_solution(input_orario, teacher, time_1, time_2, max_iterations=100):
    orario = input_orario.copy()
    permute_history = []
    c1 = logic.classe(teacher=teacher, day_hour=time_1)
    c2 = logic.classe(teacher=teacher, day_hour=time_2)
    seen = set()

    conflict1, conflict2 = logic.permute(orario, c1, c2)
    permute_history.append( (c1, c2) )
    seen.add(c2)
    conflicts = conflict1[0].size != 0 or conflict2[0].size != 0
    iterations = 0

    conflicting_teacher = teacher 
    conflicting_time = None

    while conflicts and iterations < max_iterations:
        # find which teacher different from the current one has conflicts
        if conflict1[0].size != 0:
            conflicting_teacher = list(set(conflict1[0]) - set([conflicting_teacher]))[0]
            conflicting_time = conflict1[1]
        elif conflict2[0].size != 0:
            conflicting_teacher = list(set(conflict2[0]) - set([conflicting_teacher]))[0]
            conflicting_time = conflict2[1]

        free_day_hour = logic.find_next_available_slot(orario, conflicting_teacher, seen)
        c1 = logic.classe(teacher=conflicting_teacher, day_hour=conflicting_time)
        c2 = logic.classe(teacher=conflicting_teacher, day_hour=free_day_hour)
        if not free_day_hour:
            seen.add(c2)
            iterations += 1
            continue
        permutation_allowed = logic.allowed_permutation(orario, c1, c2, curricula_data.not_allowed)
        if not permutation_allowed:
            seen.add(c2)
            iterations += 1
            continue
        conflict1, conflict2 = logic.permute(orario, c1, c2)
        permute_history.append( (c1, c2) )
        seen.add(c1)            
        conflicts = conflict1[0].size != 0 or conflict2[0].size != 0
        if not conflicts:
            # print("No more conflicts!")
            conflicts = False
        iterations += 1

    if iterations == max_iterations:
        return None, None
    else:
        return orario, permute_history

orario_path = './data/inga_imp.csv'
orario = pd.read_csv(orario_path)
orario.set_index("teacher", inplace=True)
# orario.to_csv(orario_path)
curricula_data = curricula.curricula('./data/docente_classes.csv')

conflicting_teacher = 'SOLE A.'
conflicting_hour_1 = 'GIO8'

empty_slots = logic.find_all_available_slots(orario, conflicting_teacher)

for conflicting_hour_2 in ['LUN14']: #empty_slots:
    sol, history = find_solution(orario, conflicting_teacher, conflicting_hour_1, conflicting_hour_2, 200)
    if not history:
        print(conflicting_hour_2, 'no solution found')
        continue
    quality = logic.schedule_quality(sol)
    print(f'{conflicting_hour_2}: {quality}')
    file.dump_to_html(sol, history, f'{conflicting_hour_1}_{conflicting_hour_2}.html')
