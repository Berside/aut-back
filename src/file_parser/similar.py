import re
from .units import extract_numbers_with_units, remove_quantities

def normalize(s):
    """Нормализует строку для сравнения: убирает пробелы, заменяет ± на +-, нормализует буквы и тд."""
    if not s:
        return ""

    # Пробелы
    # s = re.sub(r'\s+', '', s)

    # Длинное тире - короткое тире
    s = s.replace('—', '-')

    # ± на +-
    s = s.replace('+-', '±')


    # Точка - запятая
    s = s.replace(',', '.')

    # Кириллица-латиница
    upper_map = {
        'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
        'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
        'Х': 'X', 
    }
    trans_upper = str.maketrans(upper_map)
    s = s.translate(trans_upper)

    # Нижний - верхний регистр
    s = s.lower()

    lower_map = {
        'a': 'а', 'b': 'б', 'e': 'е', 'k': 'к', 'm': 'м',
        'н': 'h', 'o': 'о', 'p': 'р', 'c': 'с', 't': 'т',
        'x': 'х', 'y': 'у'
    }
    trans_lower = str.maketrans(lower_map)
    s = s.translate(trans_lower)

    # Буква З - цифра 3 
    s = s.replace('з', '3')
    s = s.replace('о', '0') 
    s = s.replace('o', '0') 
    
    return s


def are_similar(id1, id2):
    """Проверяет, похожи ли два обозначения."""
    if not id1 or not id2:
        return False

    id1 = re.sub(r'\s+', '', id1) #todo ВОЗМОЖНО тут проблема с пробелами (например, когда длинное и короткое тире с одним пробелом перед или после)
    id2 = re.sub(r'\s+', '', id2)

    units1 = set(extract_numbers_with_units(id1))
    units2 = set(extract_numbers_with_units(id2))

    text1 = remove_quantities(id1)
    text2 = remove_quantities(id2)

    norm1 = normalize(text1)
    norm2 = normalize(text2)

    if norm1 != norm2:
        return False

    #Тексты совпали - проверяем величины
    if units1 and units2:
        return units1.issubset(units2) or units2.issubset(units1)

    if units1 or units2:
        return False

    return True