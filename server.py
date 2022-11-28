import argparse
import json
import sys
from http import HTTPStatus
from time import sleep

from common.jim_protocol.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from common.jim_protocol.jim_base import Actions, Keys
from common.jim_protocol.jim_server import JIMServer
from config import CommonConf, ServerConf
from log.decorator import log
from log.server_log_config import call_logger, main_logger


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
        type=type(CommonConf.DEFAULT_PORT),
        default=CommonConf.DEFAULT_PORT,
    )
    args = parser.parse_args()
    if not 1023 < args.port < 65536:
        main_logger.critical(
            f"Попытка запуска сервера с неподходящим номером порта: {args.port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)
    return args.address, args.port


@log(call_logger)
def print_msg(msg: dict, addr: tuple):
    msg_formatted = json.dumps(msg, indent=2, ensure_ascii=False)
    print(f"Сообщение от клиента {':'.join(map(str, addr))}: {msg_formatted}", end="\n\n")


@log(call_logger)
def run_server():
    conn_params = parse_args()
    with JIMServer(conn_params) as jim_server:
        while True:
            try:
                jim_server.listen()
                break
            except OSError:
                main_logger.info(f"Ожидается освобождение сокета {':'.join(map(str, conn_params))}...")
                sleep(1)

        while True:
            try:
                msg = jim_server.recv()
                jim_server.validate_msg(msg)
                if msg.get(Keys.ACTION) == Actions.QUIT:
                    response = jim_server.make_response_msg(HTTPStatus.OK)
                    main_logger.debug(f"Отправлен ответ {response} клиенту {':'.join(map(str, jim_server.addr))}")
                    jim_server.send(response)
                    jim_server.close()
                    break

                print_msg(msg, jim_server.addr)
                response = jim_server.make_response_msg(HTTPStatus.OK)
                main_logger.debug(f"Отправлен ответ {response} клиенту {':'.join(map(str, jim_server.addr))}")
                jim_server.send(response)
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                error_msg_response = jim_server.make_response_msg(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(ex))
                jim_server.send(error_msg_response)
                main_logger.error(str(ex))


if __name__ == "__main__":
    main_logger.info("Приложение запущено.")
    try:
        run_server()
    except KeyboardInterrupt:
        main_logger.info("Работа клиента была принудительно завершена.")
        sys.exit(0)
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as ex:
        main_logger.warning(f"Произошел разрыв соединения ({ex})")
        sys.exit(0)
    except Exception as ex:
        main_logger.critical(str(ex))
        sys.exit(1)
