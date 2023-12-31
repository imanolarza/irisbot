import json

file_path = 'tema_diario.json'

def load_json():
  with open(file_path, 'r', encoding='utf-8') as json_file:
    res = json.load(json_file)

    return res

def update_json(col, value):
  with open(file_path, 'r+', encoding='utf-8') as json_file:
    res = json.load(json_file)
    res[col] = value

    json_file.seek(0)
    json.dump(res, json_file)
    json_file.truncate()

    return res