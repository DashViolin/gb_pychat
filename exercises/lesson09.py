# Урок 9, задания №№ 1-4.

import platform
import subprocess
from collections import defaultdict
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from itertools import zip_longest

from tabulate import tabulate


def ping(host: str | IPv4Address | IPv6Address, pings_count: int = 1):
    """
    Функция работает как для Linux, так и для Windows систем. Так как процесс ping в Windows
    возвращает в любом случае 0, приходится не ориентироваться на код возврата искать в выводе
    процесса присутсвие токена "TTL" для Windows и "ttl" для Linux соответственно.
    Дополнительно проводится валидация IP адреса, неверный IP вызывает ValueError.
    """
    addr = None
    if isinstance(host, str):
        if host.replace(".", "").isdigit() or ":" in host:
            addr = ip_address(host)
    addr = addr or host
    count_param = f"-n" if platform.system().lower() == "windows" else f"-c"
    command = ["ping", count_param, str(pings_count), str(addr)]
    try:
        result = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return b"TTL" in result or b"ttl" in result
    except subprocess.CalledProcessError:
        return False


def host_ping(hosts: list):
    for host in hosts:
        try:
            if ping(host):
                print(f"Host '{host}' is reachable")
            else:
                print(f"Host '{host}' is unreachable")
        except ValueError as ex:
            print(f"Host {ex}")


def host_range_ping_tab(hosts: list, tablefmt: str = "rounded_grid"):
    col_ok = "REACHABLE"
    col_off = "UNREACHABLE"
    col_invalid = "INVALID IP"
    header = [col_ok, col_off]
    table_data = defaultdict(list)
    for host in hosts:
        try:
            if ping(host):
                table_data[col_ok].append(host)
            else:
                table_data[col_off].append(host)
        except ValueError as ex:
            if col_invalid not in header:
                header.append(col_invalid)
            table_data[col_invalid].append(host)
    columns = (table_data[header[index]] for index in range(len(header)))
    table_rows = zip_longest(*columns)
    print(tabulate(table_rows, headers=header, tablefmt=tablefmt))


def host_range_ping(subnet: str, start: int = 0, stop: int = 255, table_view: bool = True):
    """
    Параметр subnet должен быть строкой в формате: 'Х.Х.Х.0/Y',
    где X - значимый октет подсети, Y - маска подсети, иначе возникнет исключение.
    """
    if not all((0 < start <= 255, 0 < stop <= 255)):
        raise ValueError("Аргументы start и stop должны быть в диапазоне [0,255]")
    if start > stop:
        start, stop = stop, start
    valid_subnet = ip_network(subnet)
    address_pool = list(valid_subnet.hosts())[start - 1 : stop]
    if table_view:
        host_range_ping_tab(address_pool)
    else:
        host_ping(address_pool)


if __name__ == "__main__":
    test_data = [
        "127.0.0.1",
        "333.333.333.333",
        ip_address("8.8.8.8"),
        "192.168.200.132",
        "slkdjflkjfljefl.com",
        "yandex.ru",
        "2001:db8::1000",
        "ff02::5678%1",
        "::1.2.3.4:",
        "::127.0.0.1",
        "::ffff:127.0.0.1",
        ":::",
        ip_address("::1"),
    ]

    host_ping(test_data)
    print()
    host_range_ping_tab(test_data)
    print()
    host_range_ping("192.168.1.0/24", 222, 224, table_view=False)
    print()
    host_range_ping("192.168.88.0/24", 224, 222, table_view=True)
