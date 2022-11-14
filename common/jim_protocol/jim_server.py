from contextlib import ContextDecorator
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket

from common import config
from log.server_log_config import logging

from .jim_base import Actions, JIMBase, Keys

logger = logging.getLogger(config.Server.MAIN_LOGGER_NAME)


class JIMServer(JIMBase, ContextDecorator):
    def __init__(self, conn_params) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.conn_params = conn_params
        super().__init__()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        logger.info("Закрываю соединение...")
        self.close()

    def listen(self):
        self.sock.bind(self.conn_params)
        logger.info(f"Сервер запущен на {':'.join(map(str, self.conn_params))}.")
        self.sock.listen(config.Server.MAX_CONNECTIONS)
        self.client, self.addr = self.sock.accept()
        logger.info(f"Подключился клиент {':'.join(map(str, self.addr))}")

    def close(self):
        self.sock.close()

    def recv(self):
        raw_data = self.client.recv(self.package_length)
        return self._load_msg(raw_data)

    def send(self, msg):
        msg_raw_data = self._dump_msg(msg)
        self.client.send(msg_raw_data)

    def make_probe_msg(self):
        msg = {Keys.ACTION: Actions.PROBE}
        return msg

    def make_response_msg(self, code: HTTPStatus, description: str = ""):
        description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        return msg
