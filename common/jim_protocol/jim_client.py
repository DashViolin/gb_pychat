from contextlib import ContextDecorator
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket

from log.client_log_config import call_logger, main_logger
from log.decorator import log

from .jim_base import Actions, JIMBase, Keys


class JIMClient(JIMBase, ContextDecorator):
    @log(call_logger)
    def __init__(self, conn_params, username) -> None:
        self.username = username
        self.conn_params = conn_params
        self.sock = socket(AF_INET, SOCK_STREAM)
        super().__init__()

    def __str__(self):
        return "JIM_client_object"

    @log(call_logger)
    def __enter__(self):
        return self

    @log(call_logger)
    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    @log(call_logger)
    def connect(self):
        self.sock.connect(self.conn_params)
        presense = self.make_presence_msg()
        response = self.send_msg(presense)
        if response.get(Keys.RESPONSE) == HTTPStatus.OK:
            return True, response
        return False, response

    @log(call_logger)
    def close(self):
        self.sock.close()

    @log(call_logger)
    def send_msg(self, msg: dict):
        msg_raw_data = self._dump_msg(msg)
        self.sock.send(msg_raw_data)
        raw_resp_data = self.sock.recv(self.package_length)
        return self._load_msg(raw_resp_data)

    @log(call_logger)
    def make_presence_msg(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        return msg

    @log(call_logger)
    def make_authenticate_msg(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        return msg

    @log(call_logger)
    def make_quit_msg(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        return msg

    @log(call_logger)
    def make_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MSG: message,
            Keys.ENCODING: self.encoding,
        }
        return msg

    @log(call_logger)
    def make_join_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        return msg

    @log(call_logger)
    def make_leave_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        return msg
