# 1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
# клиент отправляет запрос серверу;
# сервер отвечает соответствующим кодом результата.
# Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
#
# Функции клиента:
# - сформировать presence-сообщение;
# - отправить сообщение серверу;
# - получить ответ сервера;
# - разобрать сообщение сервера;
# - параметры командной строки скрипта client.py <addr> [<port>]:
#   - addr — ip-адрес сервера;
#   - port — tcp-порт на сервере, по умолчанию 7777.

import argparse

from common import config
from common import JIMClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="JSON instant messaging (JIM) client.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="IP address for server listener",
        type=type(config.Client.DEFAULT_SERVER_IP),
        default=config.Client.DEFAULT_SERVER_IP,
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


def main():
    conn_params = parse_args()
    jim_client = JIMClient(conn_params, "user")
    jim_client.send_presence()

    try:
        while True:
            msg_text = str(input("Введите текст (или exit для выхода): "))
            if msg_text.strip() == config.Common.EXIT_WORD:
                jim_client.close()
                return

            resp_msg = jim_client.send_msg("user_dest", msg_text)
            print(f"Сообщение от сервера: '{resp_msg}'", end="\n\n")
    except Exception:
        pass
    finally:
        jim_client.close()


if __name__ == "__main__":
    main()
