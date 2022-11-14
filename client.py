import argparse
import sys
from time import sleep

from common import config
from common.jim_protocol.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from common.jim_protocol.jim_client import JIMClient
from log.client_log_config import logging

logger = logging.getLogger(config.Client.MAIN_LOGGER_NAME)


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
    if not 1023 < args.port < 65536:
        logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.address, args.port


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
                logger.info(f"Пытаюсь подключиться как {username} к серверу {':'.join(map(str, conn_params))}...")
                sleep(1)

        try:
            jim_client.validate_msg(response)
            logger.debug(f"Получен ответ от сервера: {response}")
        except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
            logger.error(ex)

        while True:
            try:
                msg_text = str(input("Введите текст (или exit для выхода): "))
                if msg_text.strip() == config.Common.EXIT_WORD:
                    jim_client.close()
                    break

                msg = jim_client.make_msg("user_dest", msg_text)
                response = jim_client.send_msg(msg)
                jim_client.validate_msg(response)
                logger.debug(f"Получен ответ от сервера: {response}")
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                logger.error(ex)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Работа клиента была принудительно завершена.")
        sys.exit(0)
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as ex:
        logger.warning(f"Произошел разрыв соединения ({ex})")
        sys.exit(0)
    except Exception as ex:
        logger.critical(str(ex))
        sys.exit(1)
