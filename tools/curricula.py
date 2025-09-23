import pandas as pd
import numpy as np

class curricula:
    ALLOWED_LUN14 = ['3E', '4E', '5E', '1L', '1I', '2L', '2I', '3L']

    def __init__(self, file_path):
        docentes_data = pd.read_csv(file_path)
        self.professors = sorted(list(set(docentes_data['Identificativo']) - set([np.nan])))
        self.total_classes = sorted(list(set(docentes_data['Classi']) - set([np.nan])))
        self.not_allowed = {
            'LUN14': set(self.total_classes) - set(self.ALLOWED_LUN14),
            'MER14': set(self.total_classes) - set(self.ALLOWED_LUN14), 
            'VEN14': set(self.total_classes) - set(['3L'])
        }
        # Create a priority queue with docentes_data
        # reaches with lower classes are to be dispatcher first
        

    def get_teachers_and_classes(self):
        return self.professors
    
    def get_classes(self):
        return self.total_classes

