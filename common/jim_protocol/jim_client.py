from abc import abstractmethod
from dataclasses import dataclass
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket

from .jim_base import JIMBase
from .jim_base import Keys
from .jim_base import Actions


class JIMClient(JIMBase):
    def __init__(self, conn_params, username) -> None:
        self.username = username
        self.conn_params = conn_params
        self.sock = socket(AF_INET, SOCK_STREAM)
        super().__init__()

    def connect(self):
        self.sock.connect(self.conn_params)
        presense = self.make_presence_msg()
        response = self.send_msg(presense)
        if response.get(Keys.RESPONSE) == HTTPStatus.OK:
            return True, response
        return False, response

    def close(self):
        self.sock.close()

    def send_msg(self, msg: dict):
        msg_raw_data = self._dump_msg(msg)
        self.sock.send(msg_raw_data)
        raw_resp_data = self.sock.recv(self.package_length)
        return self._load_msg(raw_resp_data)

    def make_presence_msg(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        return msg

    def make_authenticate_msg(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        return msg

    def make_quit_msg(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        return msg

    def make_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MSG: message,
            Keys.ENCODING: self.encoding,
        }
        return msg

    def make_join_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        return msg

    def make_leave_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        return msg
