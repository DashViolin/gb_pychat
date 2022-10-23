# Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата.
# Для этого:
#  - Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число,
# третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом,
# отсутствующим в кодировке ASCII (например, €);
#  - Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
# При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
# а также установить возможность работы с юникодом: allow_unicode = True;
#  - Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.

import pathlib

import yaml

data = {
    "key1": ["list_item1", "list_item2", 100.0, True],
    "key2": 1000,
    "key3": {"price1": "100 €", "price2": "200 \u00A3", "price3": "300 \u20BD"},
}

base_dir = pathlib.Path.cwd() / "exercises" / "2_file_data_store"
data_file = base_dir / "example.yml"


with open(data_file, "w", encoding="utf-8") as file:
    yaml.dump(data, file, allow_unicode=True, default_flow_style=False)

with open(data_file, "r", encoding="utf-8") as file:
    loaded_data = yaml.safe_load(file)

assert loaded_data == data
