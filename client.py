import argparse
import sys
from time import sleep

from common.jim_protocol.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from common.jim_protocol.jim_client import JIMClient
from config import ClientConf, CommonConf
from log.client_log_config import call_logger, main_logger
from log.decorator import log


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
    args = parser.parse_args()
    if not 1023 < args.port < 65536:
        main_logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.address, args.port


@log(call_logger)
def main():
    conn_params = parse_args()
    username = "user"
    with JIMClient(conn_params, username) as jim_client:
        while True:
            try:
                conn_is_ok, response = jim_client.connect()
                if conn_is_ok:
                    break
            except ConnectionRefusedError:
                main_logger.info(f"Пытаюсь подключиться как {username} к серверу {':'.join(map(str, conn_params))}...")
                sleep(1)

        try:
            jim_client.validate_msg(response)
            main_logger.debug(f"Получен ответ от сервера: {response}")
        except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
            main_logger.error(ex)

        main_logger.info(f"Успешно подключен к серверу {':'.join(map(str, conn_params))} от имени {username}")
        while True:
            try:
                msg_text = str(input("Введите текст (или exit для выхода): "))
                if msg_text.strip() == CommonConf.EXIT_WORD:
                    quit = jim_client.make_quit_msg()
                    response = jim_client.send_msg(quit)
                    jim_client.validate_msg(response)
                    main_logger.info(f"Получен ответ от сервера: {response}")
                    jim_client.close()
                    break

                msg = jim_client.make_msg("user_dest", msg_text)
                response = jim_client.send_msg(msg)
                jim_client.validate_msg(response)
                main_logger.info(f"Получен ответ от сервера: {response}")
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.error(ex)


if __name__ == "__main__":
    try:
        main_logger.info("Приложение запущено.")
        main()
    except KeyboardInterrupt:
        main_logger.info("Работа клиента была принудительно завершена.")
        sys.exit(0)
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as ex:
        main_logger.warning(f"Произошел разрыв соединения ({ex})")
        sys.exit(0)
    except Exception as ex:
        main_logger.critical(str(ex))
        sys.exit(1)
