import re

units = {
    'a': 'а',
    'а': 'а',
    'в': 'v_cyr',
    'b': 'v_cyr',

    'v': 'v',
    'w': 'w',
    'вт': 'vt_cyr',
    'ом': 'ohm',
    'ком': 'kohm',
    'мкф': 'uf',
    '%': 'perc'
}

units_keys = list(units.keys())

def normalize_unit(unit):
    u = unit.lower()
    return units.get(u, u)

def extract_numbers_with_units(s):
    """Извлекает все числа, после которых стоит единица измерения"""
    if not s:
        return []

    #Паттерн - число (целое или с плав. точкой), затем опционально пробелы, затем юнит
    units_pattern = '|'.join(re.escape(u) for u in units_keys)
    pattern = r'(\d+[.,]?\d*)\s*(' + units_pattern + r')(?=[^a-zA-Zа-яА-Я]|$)'
    matches = re.finditer(pattern, s, re.IGNORECASE)

    result = []

    for m in matches:
        num_str = m.group(1).replace(',', '.')
        unit_raw = m.group(2)
        canonical = normalize_unit(unit_raw)

        try:
            num = float(num_str)
            result.append((num, canonical))
        except ValueError:
            pass
    return result



def remove_quantities(s):
    """Удаляет из строки все числа с единицами измерения"""

    if not s: 
        return None
    units_pattern = '|'.join(re.escape(u) for u in units_keys)
    pattern = r'\d+[.,]?\d*\s*(' + units_pattern + r')(?=[^a-zA-Zа-яА-Я]|$)'
    return re.sub(pattern, '', s, flags=re.IGNORECASE)