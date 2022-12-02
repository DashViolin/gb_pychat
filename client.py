import argparse
import sys
from http import HTTPStatus
from time import sleep

from config import ClientConf, CommonConf
from jim.base import Keys
from jim.client import JIMClient
from jim.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
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
        type=type(CommonConf.DEFAULT_PORT),
        default=CommonConf.DEFAULT_PORT,
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Username",
        type=str,
        default="guest",
    )
    parser.add_argument(
        "-r",
        "--reader",
        help="Reader working mode, for data recieve only",
        type=bool,
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()
    if not 1023 < args.port < 65536:
        main_logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.reader, args.user, args.address, args.port


if __name__ == "__main__":
    try:
        main_logger.info("Приложение запущено.")
        is_reader, username, *conn_params = parse_args()
        with JIMClient(tuple(conn_params), username=username, mode=is_reader) as jim_client:
            while True:
                server_name = ":".join(map(str, conn_params))
                try:
                    response = jim_client.connect()
                    jim_client.validate_msg(response)
                    main_logger.debug(f"Получен ответ от сервера: {response}")
                    match response[Keys.RESPONSE]:
                        case HTTPStatus.OK:
                            main_logger.info(f"Успешно подключен к серверу {server_name} от имени {username}")
                            break
                        case HTTPStatus.FORBIDDEN:
                            main_logger.warning(f"Сервер {server_name} отказал в подключении: {response}")
                            raise KeyboardInterrupt
                        case _:
                            pass
                except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                    main_logger.info(f"Не удалось подключиться от имени {username} к серверу {server_name} ({str(ex)})")
                    raise KeyboardInterrupt
                except ConnectionRefusedError as ex:
                    main_logger.info(f"Пытаюсь подключиться как {username} к серверу {server_name}...")
                    sleep(1)

            jim_client.mainloop()

    except KeyboardInterrupt:
        main_logger.info("Работа клиента была принудительно завершена.")
        sys.exit(0)
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as ex:
        main_logger.warning(f"Произошел разрыв соединения ({ex})")
        sys.exit(0)
    except Exception as ex:
        main_logger.critical(str(ex))
        sys.exit(1)
