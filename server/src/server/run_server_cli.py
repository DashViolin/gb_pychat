import argparse
import sys
import warnings

from common.decorators import log
from server.config import ServerConf
from server.logger_conf import call_logger, main_logger
from server.transport import JIMServer


@log(call_logger)
def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch JSON instant messaging (JIM) server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="IP address for server listener",
        type=type(ServerConf.DEFAULT_LISTENER_ADDRESS),
        default=ServerConf.DEFAULT_LISTENER_ADDRESS,
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port for server listener",
        type=type(ServerConf.DEFAULT_PORT),
        default=ServerConf.DEFAULT_PORT,
    )
    args = parser.parse_args()
    if not 1023 < args.port < 65536:
        main_logger.critical(
            f"Попытка запуска сервера с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.address, args.port


def run():
    main_logger.info("Приложение запущено.")
    try:
        ip, port = parse_args()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with JIMServer(ip, port) as jim_server:
                jim_server.start_server()
    except KeyboardInterrupt:
        main_logger.info("Работа сервера была принудительно завершена.")
        sys.exit(0)
    except Exception as ex:
        main_logger.critical(str(ex))
        sys.exit(1)


if __name__ == "__main__":
    run()
