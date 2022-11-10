import argparse
import json

from common import JIMClient, config


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
    username = "user"
    jim_client = JIMClient(conn_params, username)
    conn_is_ok, response = jim_client.connect()
    response = json.dumps(response, indent=2)
    print(f"\nСообщение от сервера: {response}", end="\n\n")
    if conn_is_ok:
        try:
            while True:
                msg_text = str(input("Введите текст (или exit для выхода): "))
                if msg_text.strip() == config.Common.EXIT_WORD:
                    jim_client.close()
                    break
                msg = jim_client.make_msg("user_dest", msg_text)
                response = json.dumps(jim_client.send_msg(msg), indent=2)
                print(f"\nСообщение от сервера: {response}", end="\n\n")
        except Exception:
            pass
        finally:
            jim_client.close()


if __name__ == "__main__":
    main()
