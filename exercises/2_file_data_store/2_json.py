# 2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах.
# Написать скрипт, автоматизирующий его заполнение данными. Для этого:
#  - Создать функцию write_order_to_json(), в которую передается 5 параметров —
# товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date).
# Функция должна предусматривать запись данных в виде словаря в файл orders.json.
# При записи данных указать величину отступа в 4 пробельных символа;
#  - Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра.

import pathlib
import json
import datetime


base_dir = pathlib.Path.cwd() / "exercises" / "2_file_data_store"
orders_file = base_dir / "orders.json"


def write_order_to_json(item: str, quantity: int, price: float, buyer: str, date: datetime.date):
    data = {"item": item, "quantity": quantity, "price": price, "buyer": buyer, "date": date.isoformat()}
    with open(orders_file) as file:
        orders = json.load(file)
    orders["orders"].append(data)
    with open(orders_file, "w") as file:
        json.dump(orders, file, indent=4)


write_order_to_json(item="Notebook", quantity=1, price=1000.0, buyer="user1", date=datetime.date.today())
write_order_to_json(item="USB Flash Drive", quantity=3, price=10.5, buyer="user2", date=datetime.date.today())
write_order_to_json(item="Intel SSD", quantity=1, price=248.4, buyer="user1", date=datetime.date.today())
write_order_to_json(item="DVD-RW", quantity=12, price=30.0, buyer="user4", date=datetime.date.today())
