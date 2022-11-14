import argparse
import json
from time import sleep

from common import JIMClient, config
from common import NonDictInputError
from common import IncorrectDataRecivedError
from common import ReqiuredFieldMissingError


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


def print_response(response):
    response_formatted = json.dumps(response, indent=2, ensure_ascii=False)
    print(f"\nСообщение от сервера: {response_formatted}", end="\n\n")


def main():
    conn_params = parse_args()
    username = "user"
    jim_client = JIMClient(conn_params, username)
    while True:
        try:
            conn_is_ok, response = jim_client.connect()
            if conn_is_ok:
                break
        except ConnectionRefusedError:
            print("Пытаюсь подключиться к серверу...")
            sleep(1)

    try:
        jim_client.validate_msg(response)
        print_response(response)
    except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
        print(ex)
    try:
        while True:
            try:
                msg_text = str(input("Введите текст (или exit для выхода): "))
                if msg_text.strip() == config.Common.EXIT_WORD:
                    jim_client.close()
                    break

                msg = jim_client.make_msg("user_dest", msg_text)
                response = jim_client.send_msg(msg)
                jim_client.validate_msg(response)
                print_response(response)
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                print(ex)
    except (ConnectionResetError, KeyboardInterrupt, BrokenPipeError, ValueError):
        print("\nЗакрываю соединение...")
        jim_client.close()


if __name__ == "__main__":
    main()
