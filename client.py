import argparse
import sys

from config import ClientConf
from jim.client import JIMClient
from logger.client_log_config import call_logger, main_logger
from logger.decorator import log


@log(call_logger)
def parse_args():
    parser = argparse.ArgumentParser(
        description="JSON instant messaging (JIM) client.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="IP address for server listener",
        type=type(ClientConf.DEFAULT_SERVER_IP),
        default=ClientConf.DEFAULT_SERVER_IP,
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port for server listener",
        type=type(ClientConf.DEFAULT_PORT),
        default=ClientConf.DEFAULT_PORT,
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Username",
        type=str,
        default="guest",
    )
    args = parser.parse_args()
    if not 1023 < args.port < 65536:
        main_logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.user, args.address, args.port


if __name__ == "__main__":
    try:
        username, ip, port = parse_args()
        with JIMClient(ip=ip, port=port, username=username) as jim_client:
            jim_client.run()

    except KeyboardInterrupt:
        main_logger.info("Работа клиента была принудительно завершена.")
        sys.exit(0)
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as ex:
        main_logger.warning(f"Произошел разрыв соединения ({ex})")
        sys.exit(0)
    # except Exception as ex:
    #     main_logger.critical(str(ex))
    #     sys.exit(1)
