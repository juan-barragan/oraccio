# %%
from monitor import dispatcher

file_path = './data/docente_classes.csv'

days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
hours = list(range(8,15))

orario = {
    f'{day}{hour}': [] for day in days for hour in hours     
}

resource_dispatcher = dispatcher.ressource(file_path, days, hours)

for k in orario:
    resource = resource_dispatcher.available_for_time(k)
    while resource is not None:
        orario[k].append(resource)
        resource = resource_dispatcher.available_for_time(k)
    

# %%
import pandas as pd

def orario_to_dataframe(orario):
    orario_dico = { (k, v[1][0]): v[0] for k in orario for v in orario[k] }

    horario_dataframe = {
        'teacher': []
    }
    horario_dataframe.update({f'{day}{hour}': [] for day in days for hour in hours})

    for teacher in resource_dispatcher.professors:
        horario_dataframe['teacher'].append(teacher)
        for day in days:
            for hour in hours:
                day_hour = f'{day}{hour}'
                if (day_hour, teacher) in orario_dico:
                    horario_dataframe[day_hour].append(orario_dico[(day_hour, teacher)])
                else:
                    horario_dataframe[day_hour].append('') 
    horario_dataframe = pd.DataFrame(horario_dataframe)
    horario_dataframe.sort_values(by='teacher', inplace=True)
    return horario_dataframe

# %%




# %%
resource_dispatcher.resources_still_availables()

# %%
ds = orario_to_dataframe(orario)

# %%
ds.to_csv('./orario_v2.csv', index=False)

# %%



