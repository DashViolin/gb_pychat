import argparse
import json
import sys
from http import HTTPStatus
from time import sleep

from common import config
from common.jim_protocol.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from common.jim_protocol.jim_server import JIMServer


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


def print_msg(msg: dict, addr: tuple):
    msg_formatted = json.dumps(msg, indent=2, ensure_ascii=False)
    print(f"Сообщение от клиента {':'.join(map(str, addr))}: {msg_formatted}", end="\n\n")


def run_server():
    conn_params = parse_args()
    with JIMServer(conn_params) as jim_server:
        try:
            jim_server.listen()
        except OSError:
            print("Ожидается освобождение сокета...")
            sleep(1)

        while True:
            try:
                msg = jim_server.recv()
                jim_server.validate_msg(msg)
                print_msg(msg, jim_server.addr)
                response = jim_server.make_response_msg(HTTPStatus.OK)
                jim_server.send(response)
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                error_msg_response = jim_server.make_response_msg(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(ex))
                jim_server.send(error_msg_response)
                print(ex)


if __name__ == "__main__":
    try:
        run_server()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(0)
