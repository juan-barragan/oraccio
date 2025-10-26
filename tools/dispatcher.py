import pandas as pd
from collections import defaultdict

class dispatcher:
    days = ['LUN', 'MAR', 'MER', 'GIO', 'VEN']
    hours = list(range(8,15))  # 6 hours per day

    def __init__(self, csv_file_path):
        df = pd.read_csv(csv_file_path)
        self.df = df.dropna(subset=['Identificativo', 'Materia', 'Classi', 'N.Ore'])
        # storing professors, subjects, classes and hours
        self.df['N.Ore'] = self.df['N.Ore'].astype(int)
        self.teachers = self.df['Identificativo'].unique()
        self.classes = self.df['Classi'].unique()
        self.class_available = {
            class_name: {(d,h): True for d in self.days for h in self.hours} for class_name in self.classes
        }
        self.professor_available = {
            teacher: {(d,h): True for d in self.days for h in self.hours} for teacher in self.teachers
        }

        self.hours_per_week = defaultdict(int)
        self.assignments = defaultdict(int)
        for _, row in df.iterrows():
            teacher = row['Identificativo']
            class_name = row['Classi']
            if pd.isna(class_name) or class_name == '':
                print(f"Warning: Missing class for teacher {teacher}, skipping entry.")
                continue
            subject = row['Materia']
            hours = row['N.Ore']
            key = (teacher, class_name, subject)
            self.assignments[key] += hours
            self.hours_per_week[class_name] += int(hours)


    def get_resource(self):
        items = sorted(self.assignments.items(), key=lambda x: x[1])
        key = None
        if len(items)>0:
            key =  items[0]
            self.assignments[key] -= 1
            if self.assignments[key]==0:
                del self.assignments[key]

        return key