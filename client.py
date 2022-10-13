print("Задание 1:")
# 1. Каждое из слов "разработка", "сокет", "декоратор" представить в строковом формате и проверить тип и содержание соответствующих переменных.
# Затем с помощью онлайн-конвертера преобразовать строковые представление в формат Unicode и также проверить тип и содержимое переменных.

a = "разработка"
b = "сокет"
c = "декоратор"

for var in (a, b, c):
    print(type(var), var, len(var), sep="\n", end="\n")


print("\nЗадание 2:")
# 2. Каждое из слов "class", "function", "method" записать в байтовом типе без преобразования в последовательность кодов
# (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.

a = b"class"
b = b"function"
c = b"method"

for var in (a, b, c):
    print(type(var), var, len(var), sep="\n", end="\n")


print("\nЗадание 3:")
# 3. Определить, какие из слов "attribute", "класс", "функция", "type" невозможно записать в байтовом типе.

for word in ("attribute", "класс", "функция", "type"):
    try:
        bytes(word, encoding="ascii")
    except ValueError:
        print(f'Unable to convert "{word}" as bytes type.')


print("\nЗадание 4:")
# 4. Преобразовать слова "разработка", "администрирование", "protocol", "standard" из строкового представления в байтовое
# и выполнить обратное преобразование (используя методы encode и decode).

for word in ("разработка", "администрирование", "protocol", "standard"):
    print(enc_word := word.encode("utf8"), enc_word.decode("utf8"), sep="\n", end="\n")


print("\nЗадание 5:")
# 5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый тип на кириллице.

import subprocess

for site in ("yandex.ru", "youtube.com"):
    args = ["ping", "-c", "4", site]
    ping = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in ping.stdout:
        print(line.decode("cp866").strip())


print("\nЗадание 6:")
# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками: "сетевое программирование", "сокет", "декоратор".
# Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести его содержимое.

import locale
import os

default_coding = locale.getpreferredencoding()
print(f"Default coding: {default_coding}", end="\n")

file = "test_file.txt"
data = ("сетевое программирование", "сокет", "декоратор")
with open(file, "w", encoding=default_coding) as f:
    for word in data:
        f.write(f"{word}\n")
with open(file, "r", encoding="utf8") as f:
    print(f.read())
os.remove(file)
