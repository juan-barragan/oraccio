import re
from unidecode import unidecode

def parse_docenti_section(file_path):
    docenti = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find the _docenti section
    match = re.search(r'_docenti\s*\{([^}]*)\}', content, re.DOTALL)
    if not match:
        return docenti
    section = match.group(1)
    # Split by lines and parse each line
    for line in section.strip().split('\n'):
        if not line.strip():
            continue
        # Split by tab or semicolon
        fields = re.split(r'\t|;', line)
        entry = {}
        for field in fields:
            if '=' in field:
                key, value = field.split('=', 1)
                entry[key.strip()] = value.strip().strip('"')
        if entry:
            docenti.append(entry)
    idx_docenti_dico = {
        doc['idx']: unidecode(doc['cognome'].strip()) for doc in docenti
    }
    docenti_idx_dico = {
        unidecode(doc['cognome'].strip()): doc['idx'] for doc in docenti
    }
    return idx_docenti_dico, docenti_idx_dico


def parse_materie_section(file_path):
    materie = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find the _materie section
    match = re.search(r'_materie\s*\{([^}]*)\}', content, re.DOTALL)
    if not match:
        return materie
    section = match.group(1)
    # Split by lines and parse each line
    for line in section.strip().split('\n'):
        if not line.strip():
            continue
        # Split by tab or semicolon
        fields = re.split(r'\t|;', line)
        entry = {}
        for field in fields:
            if '=' in field:
                key, value = field.split('=', 1)
                entry[key.strip()] = value.strip().strip('"')
        if entry:
            materie.append(entry)

    idx_materia_dico = {
        m['idx'].strip(): m['nome'].strip() for m in materie
    }
    materia_idx_dico = {
        m['nome'].strip(): m['idx'].strip() for m in materie
    }
    return idx_materia_dico, materia_idx_dico


def parse_classi_section(file_path):
    classi = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find the _classi section
    match = re.search(r'_classi\s*\{([^}]*)\}', content, re.DOTALL)
    if not match:
        return classi
    section = match.group(1)
    # Split by lines and parse each line
    for line in section.strip().split('\n'):
        if not line.strip():
            continue
        # Split by tab or semicolon
        fields = re.split(r'\t|;', line)
        entry = {}
        for field in fields:
            if '=' in field:
                key, value = field.split('=', 1)
                entry[key.strip()] = value.strip().strip('"')
        if entry:
            classi.append(entry)
    
    idx_class_dico = {
        cl['idx']: cl['nome'] for cl in classi
    }
    class_idx_dico = {
        cl['nome']: cl['idx'] for cl in classi
    }
    return idx_class_dico, class_idx_dico