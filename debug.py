from unidecode import unidecode
import pandas as pd
from parser import darwin, raw

def check_column_(df, column_name, total_number):
    x = df[column_name]
    x = x[~pd.isnull(x)]
    return len(x) == total_number & len(set(x)) == total_number

from collections import namedtuple

cathedra = namedtuple('cathedra', ['teacher', 'day', 'hour', 'classroom'])

def duplicated_indices_in_column(df, column_name):
    x = df[column_name]
    duplicated_indices = x[~pd.isnull(x)].index[x[~pd.isnull(x)].duplicated(keep=False)]
    return duplicated_indices

# style_this is a set of tuples (index, column)
def dump_to_html(df, style_this):
    html_string = '<table style="width:80%">'
    header = "<tr>"
    for col in df.columns:
        header += f"<th>{col}</th>"
    header += "</th></tr>"
    html_string += header
    for index, row in df.iterrows():
        html_string += "<tr>"
        for col in df.columns:
            if (index, col) in style_this:
                html_string += f'<td style="background-color:Orange;">{row[col]}</td>'
            else:
                html_string += f"<td>{row[col]}</td>" if pd.notnull(row[col]) else "<td></td>"  
        html_string += "</tr>"
    html_string += "</table>"
    return html_string

def wite_to_html_file(html, filename):
    with open(filename, "w") as f:
        f.write(html)

def permute(df, cathedra_1, cathedra_2 ):
    classroom_1 = cathedra_1.classroom
    df.loc[df['teacher'] == cathedra_1.teacher, cathedra_1.day + str(cathedra_1.hour)] = cathedra_2.classroom
    df.loc[df['teacher'] == cathedra_2.teacher, cathedra_2.day + str(cathedra_2.hour)] = classroom_1
    # Check if there are duplicates
    # first column
    fist_column_name = cathedra_1.day + str(cathedra_1.hour)
    second_column_name = cathedra_2.day + str(cathedra_2.hour)
    first_column_duplicated_indices = duplicated_indices_in_column(df, fist_column_name)
    second_column_duplicated_indices = duplicated_indices_in_column(df, second_column_name)
    first_column_names = df['teacher'][first_column_duplicated_indices].values
    second_column_names = df['teacher'][second_column_duplicated_indices].values
    return first_column_duplicated_indices, first_column_names, second_column_duplicated_indices, second_column_names

day_dico = {
    'LUN': 0,
    'MAR': 1,
    'MER': 2,
    'GIO': 3,
    'VEN': 4,
}

hour_dico = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 6
}

def materia_given_class_and_teacher(docenti_materie_dico, class_name, teacher_name):
    if teacher_name not in docenti_materie_dico:
        print(f"Teacher {teacher_name} not found.")
        return None
    if class_name not in docenti_materie_dico[teacher_name]:
        print(f"Class {class_name} not found for teacher {teacher_name}.")
        return None
    if len(docenti_materie_dico[teacher_name][class_name]) == 0:
        print(f"No subjects left for class {class_name} and teacher {teacher_name}.")
        return None
    return docenti_materie_dico[teacher_name][class_name].pop()

def write_down_activities_and_schedule(docenti_materie_dico, df_horario, name_to_idx, class_to_idx, materia_to_idx):
    activities = []
    schedule = []
    template_activity = 'idx={idx}	materia={materia}	no_giorni_successivi=0	utilizzo_str=1	classi=({class_id})	gruppi=(-1)	docenti=({teacher_id});'
    template_schedule = 'attivita={idx}	durata=1	giorno={day}	ora={hour};'
    idx = 0
    for _, row in df_horario.iterrows():
        teacher_name = row['teacher']
        teacher_id = name_to_idx.get(teacher_name, None)
        if teacher_id is None:
            print(f"Warning: Teacher '{teacher_name}' not found in name_to_idx mapping.")
            continue

        for day in ['LUN', 'MAR', 'MER', 'GIO', 'VEN']:
            for hour in [8, 9, 10, 11, 12, 13, 14]: 
                classroom = row.get(f'{day}{hour}', None)
                if pd.notnull(classroom):
                    class_id = class_to_idx.get(classroom, None)
                    if class_id is None:
                        print(f"Warning: Class '{classroom}' not found in class_to_idx mapping.")
                        continue
                    materia = materia_given_class_and_teacher(docenti_materie_dico, classroom, teacher_name)
                    if materia is None:
                        print(f"Warning: No subject found for class '{classroom}' and teacher '{teacher_name}'.")
                        continue
                    materia = materia_to_idx.get(materia, None)
                    activity = template_activity.format(idx=idx, materia=materia, class_id=class_id, teacher_id=teacher_id)
                    activities.append(activity)
                    schedule_entry= template_schedule.format(idx=idx, day=day_dico[day], hour=hour_dico[hour]) 
                    schedule.append(schedule_entry)
                    idx += 1
    return activities, schedule


# %%
# cathedra_1 = cathedra(teacher='BARBO', day='LUN', hour=8, classroom='4I')
# cathedra_2 = cathedra(teacher='BARBO', day='LUN', hour=13, classroom='5I')
# string = 'idx=0	materia=11	no_giorni_successivi=0	utilizzo_str=1	classi=({class_id})	gruppi=(-1)	docenti=({teacher_id});'
# string.format(class_id='1', teacher_id=2)

import pandas as pd

path = './data/orario sab.csv'
df = pd.read_csv(path)
dm = raw.parse_docenti_materie(pd.read_csv('./data/docente_classes.csv'))
_, name_to_idx = darwin.parse_docenti_section('./data/PATN01000Q-PROVA.drw')
_, class_to_idx = darwin.parse_classi_section('./data/PATN01000Q-PROVA.drw')
_, materia_to_idx = darwin.parse_materie_section('./data/PATN01000Q-PROVA.drw')
acxtivities, schedules = write_down_activities_and_schedule(dm, df, name_to_idx, class_to_idx, materia_to_idx)

last = -1
with open('activities.txt', 'w') as f:
    # activity = '\n'.join(acxtivities[:last])
    activity = '\n'.join(acxtivities)
    f.write(activity)
    # schedule = '\n'.join(schedules[:last])
    schedule = '\n'.join(schedules)
    f.write('\n')
    f.write(schedule)
