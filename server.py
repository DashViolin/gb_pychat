import argparse
import json
from http import HTTPStatus

from common import JIMServer, config


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
    jim_server.listen()

    try:
        while True:
            msg = jim_server.recv()
            msg_formatted = json.dumps(msg, indent=2)
            print(f"Сообщение от клиента {':'.join(map(str, jim_server.addr))}: {msg_formatted}", end="\n\n")
            response = jim_server.make_response_msg(HTTPStatus.OK)
            jim_server.send(response)
    except Exception:
        pass
    finally:
        jim_server.close()


if __name__ == "__main__":
    run_server()
