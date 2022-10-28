# 1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
# клиент отправляет запрос серверу;
# сервер отвечает соответствующим кодом результата.
# Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
#
# Функции сервера:
# - принимает сообщение клиента;
# - формирует ответ клиенту;
# - отправляет ответ клиенту;
# - имеет параметры командной строки:
#   -p <port> — TCP-порт для работы (по умолчанию использует 7777);
#   -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).

import argparse
from http import HTTPStatus

from common import config
from common import JIMServer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch JSON instant messaging (JIM) server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="IP address for server listener",
        type=type(config.Sever.DEFAULT_LISTENER_ADDRESS),
        default=config.Sever.DEFAULT_LISTENER_ADDRESS,
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port for server listener",
        type=type(config.Common.DEFAULT_PORT),
        default=config.Common.DEFAULT_PORT,
    )
    args = parser.parse_args()
    return args.address, args.port


def run_server():
    conn_params = parse_args()
    jim_server = JIMServer(conn_params)

    try:
        while True:
            msg = jim_server.recv()
            print(f"Сообщение: '{msg}' было отправлено клиентом {':'.join(map(str, jim_server.addr))}", end="\n\n")
            jim_server.send_response(HTTPStatus.OK)
    except Exception:
        pass
    finally:
        jim_server.close()


if __name__ == "__main__":
    run_server()
