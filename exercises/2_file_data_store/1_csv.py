# 1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных
# из файлов info_1.txt, info_2.txt, info_3.txt и формирующий новый "отчетный" файл в формате CSV. Для этого:
#  - Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных.
# В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
# "Изготовитель системы", "Название ОС", "Код продукта", "Тип системы". Значения каждого параметра поместить в соответствующий список.
# Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list, os_type_list.
# В этой же функции создать главный список для хранения данных отчета — например, main_data — и поместить в него
# названия столбцов отчета в виде списка: "Изготовитель системы", "Название ОС", "Код продукта", "Тип системы".
# Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);
#  - Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных
# через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;
# Проверить работу программы через вызов функции write_to_csv().

import csv
import chardet
import pathlib
import re


base_dir = pathlib.Path.cwd() / "exercises" / "2_file_data_store"
os_data_file = base_dir / "os_data.csv"
data_sources = ("info_1.txt", "info_2.txt", "info_3.txt")
data_fields = ("Изготовитель системы", "Название ОС", "Код продукта", "Тип системы")


def get_data():
    for file in data_sources:
        with open(base_dir / file, "rb") as file_descriptor:
            raw_data = file_descriptor.read()
            encoding = chardet.detect(raw_data)["encoding"]
            content = raw_data.decode(encoding)
            rows = (re.search(f"{field}.*\n", content).group(0).strip() for field in data_fields)
            items = (row.split(re.search(": +", row).group(0)) for row in rows)
            yield {key: value for key, value in items}


def write_to_csv(csv_file_path):
    with open(csv_file_path, "w") as file:
        writer = csv.DictWriter(file, fieldnames=data_fields, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for data in get_data():
            writer.writerow(data)


write_to_csv(os_data_file)
