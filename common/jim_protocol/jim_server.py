from contextlib import ContextDecorator
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket

import config
from log.decorator import log
from log.server_log_config import call_logger, main_logger

from .jim_base import Actions, JIMBase, Keys


class JIMServer(JIMBase, ContextDecorator):
    @log(call_logger)
    def __init__(self, conn_params) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.conn_params = conn_params
        super().__init__()

    def __str__(self):
        return "JIM_server_object"

    @log(call_logger)
    def __enter__(self):
        return self

    @log(call_logger)
    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    @log(call_logger)
    def listen(self):
        self.sock.bind(self.conn_params)
        main_logger.info(f"Сервер запущен на {':'.join(map(str, self.conn_params))}.")
        self.sock.listen(config.ServerConf.MAX_CONNECTIONS)
        self.client, self.addr = self.sock.accept()
        main_logger.info(f"Подключился клиент {':'.join(map(str, self.addr))}")

    @log(call_logger)
    def close(self):
        self.sock.close()

    @log(call_logger)
    def recv(self):
        raw_data = self.client.recv(self.package_length)
        return self._load_msg(raw_data)

    @log(call_logger)
    def send(self, msg):
        msg_raw_data = self._dump_msg(msg)
        self.client.send(msg_raw_data)

    @log(call_logger)
    def make_probe_msg(self):
        msg = {Keys.ACTION: Actions.PROBE}
        return msg

    @log(call_logger)
    def make_response_msg(self, code: HTTPStatus, description: str = ""):
        description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        return msg
