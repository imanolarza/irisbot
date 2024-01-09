import json

# Lugar en el que se carga la configuración del bot
file_path = 'configuracion.json'

# 
def load_json() -> dict:
    """
    Cargar en formato de diccionario el json de configuración.
    Retorna: Json en formato de diccionario python.
    """
    with open(file_path, 'r', encoding='utf-8') as json_file:
        res = json.load(json_file)

        return res

def update_json(col, value) -> dict:
    """
    Modificar archivo de configuración.
    Args:
        col: Columna a modificar.
        value: Valor de la columna a modificar.
    Retorna:
        Resultado de Json modificado en formato de diccionario.
    """
    with open(file_path, 'r+', encoding='utf-8') as json_file:
        res = json.load(json_file)
        res[col] = value

        json_file.seek(0)
        json.dump(res, json_file)
        json_file.truncate()

        return res