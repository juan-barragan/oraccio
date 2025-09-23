from collections import defaultdict
import pandas as pd

# Parse a csv containing the mapping from teachers to subjects and classes
def parse_docenti_materie(ds):
    profs = ds['Identificativo'].unique()
    content = {
        ' '.join(tid.split()[0:-1]): defaultdict(list) for tid in profs
    }
    for _, row in ds.iterrows():
        teacher_id = ' '.join(row['Identificativo'].split()[0:-1])
        number_of_classes = int(row['N.Ore']) if 'N.Ore' in row and pd.notnull(row['N.Ore']) else 0
        content[teacher_id][row['Classi']].extend(number_of_classes*[row['Materia']])
    return content