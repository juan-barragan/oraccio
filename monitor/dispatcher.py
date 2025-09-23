import pandas as pd
from collections import defaultdict

class ressource:
    def __init__(self, path: str, days: list[str], hours: list[int]) -> None:
        df = pd.read_csv(path)
        self.professors = set(df['Identificativo'].unique())
        self.classes = set(df['Classi'].unique())
        # At any given day and hour, we need to keep track of the classes and teachers already used
        # Only one teacher and one class can be assigned at the same time
        self.controller = {
            f'{d}{h}': {
                'seen_classes': set(),
                'seen_teachers' : set()
            } for d in days for h in hours
        }
        total_hours_by_prof = defaultdict(int)
        for _, row in df.iterrows():
            teacher = row['Identificativo']
            hours_for_class = row['N.Ore']
            if not pd.isnull(hours_for_class):
                hours_for_class = int(hours_for_class)
            else:
                hours_for_class = 0
            total_hours_by_prof[teacher] += hours_for_class

        self.hours_controler = dict()
        for day in days:
            for professor in self.professors:
                self.hours_controler[(professor, day)] = {
                    'benchmark' : round(total_hours_by_prof[professor]/5),
                    'used' : 0
                }
        self.stack = defaultdict(list)
        for _, row in df.iterrows():
            teacher = row['Identificativo']
            clase = row['Classi']
            materia = row['Materia']
            hours_for_class = row['N.Ore']
            if not pd.isnull(hours_for_class):
                hours_for_class = int(hours_for_class)
                self.stack[clase].extend( hours_for_class*[(teacher, materia)] )

    def available_for_time(self, day_hour: str):
        day = day_hour[:3]
        available_classes = self.classes - set(self.controller[day_hour]['seen_classes'])
        # for each available class check if a professor is available
        for clase in available_classes:
            for index, value in enumerate(self.stack[clase]):
                if value[0] not in self.controller[day_hour]['seen_teachers']:
                    if self.hours_controler[(value[0], day)]['used'] < self.hours_controler[(value[0], day)]['benchmark']:
                        self.hours_controler[(value[0], day)]['used'] += 1
                        self.controller[day_hour]['seen_teachers'].add( value[0] )
                        self.controller[day_hour]['seen_classes'].add( clase )
                        del self.stack[clase][index]
                        return (clase, value)
        return None
    

    def available_for_time_no_constrains(self, day_hour: str):
        day = day_hour[:3]
        available_classes = self.classes - set(self.controller[day_hour]['seen_classes'])
        # for each available class check if a professor is available
        for clase in available_classes:
            for index, value in enumerate(self.stack[clase]):
                if value[0] not in self.controller[day_hour]['seen_teachers']:
                    self.controller[day_hour]['seen_teachers'].add( value[0] )
                    self.controller[day_hour]['seen_classes'].add( clase )
                    del self.stack[clase][index]
                    return (clase, value)
        return None
        
    def resources_still_availables(self):
        resources = {
            k: self.stack[k] for k in self.stack if len(self.stack[k]) > 0
        }
        return resources
    
