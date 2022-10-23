import json
from dataclasses import dataclass
from datetime import datetime
from socket import socket
from socket import AF_INET
from socket import SOCK_STREAM
from http import HTTPStatus

from common import config


# Большая часть написанно - пропробовать, подумать и, возмножно, на будущее


@dataclass
class Keys:
    ACTION = "action"
    TIME = "time"
    USER = "user"
    ACCOUNT_NAME = "account_name"
    PASSWORD = "password"
    STATUS = "status"
    FROM = "from"
    TO = "to"
    ROOM = "room"
    ENCODING = "encoding"
    MESSAGE = "message"
    RESPONSE = "response"
    ALERT = "alert"
    ERROR = "error"


@dataclass
class Actions:
    AUTHENTICATE = "authenticate"
    PRESENCE = "presence"
    PROBE = "probe"
    QUIT = "quit"
    MSG = "msg"
    JOIN = "join"
    LEAVE = "leave"


class JIMBase:
    def __init__(self) -> None:
        self.encoding = config.Common.ENCODING
        self.package_length = config.Common.MAX_PACKAGE_LENGTH

    def close(self):
        self.sock.close()

    def _from_timestamp(self, timestamp: float | int):
        return datetime.fromtimestamp(timestamp).isoformat()

    def _dump(self, msg: dict) -> bytes:
        timestamp = {Keys.TIME: datetime.now().timestamp()}
        msg.update(timestamp)
        return json.dumps(msg).encode(self.encoding)

    def _load(self, data: bytes) -> dict:
        msg: dict = json.loads(data.decode(self.encoding))
        timestamp = msg.get(Keys.TIME, 0)
        msg.update({Keys.TIME: self._from_timestamp(timestamp)})
        return msg


class JIMServer(JIMBase):
    def __init__(self, conn_params) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(conn_params)
        self.sock.listen(config.Sever.MAX_CONNECTIONS)
        self.client, self.addr = self.sock.accept()
        print(f"Подключился клиент {':'.join(map(str, self.addr))}", end="\n\n")
        super().__init__()

    def recv(self):
        raw_data = self.client.recv(self.package_length)
        return self._load(raw_data)

    def _send(self, msg):
        msg_raw_data = self._dump(msg)
        self.client.send(msg_raw_data)

    def send_probe(self):
        msg = {Keys.ACTION: Actions.PROBE}
        self._send(self._dump(msg))

    def send_response(self, code: HTTPStatus, description: str = None):
        msg = {Keys.RESPONSE: code.value}
        description = description or code.phrase
        if 400 <= code.value < 600:
            msg.update({Keys.ERROR: description})
        else:
            msg.update({Keys.ALERT: description})
        self._send(msg)


class JIMClient(JIMBase):
    def __init__(self, conn_params, username) -> None:
        self.username = username
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect(conn_params)
        super().__init__()

    def close(self):
        self.sock.close()

    def _recv(self):
        raw_resp_data = self.sock.recv(self.package_length)
        return self._load(raw_resp_data)

    def _send_and_get_responce(self, msg: dict):
        msg_raw_data = self._dump(msg)
        self.sock.send(msg_raw_data)
        return self._recv()

    def send_presence(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        return self._send_and_get_responce(msg)

    def send_authenticate(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTHENTICATE,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        return self._send_and_get_responce(msg)

    def send_quit(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        return self._send_and_get_responce(msg)

    def send_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MESSAGE: message,
            Keys.ENCODING: self.encoding,
        }
        return self._send_and_get_responce(msg)

    def send_join_room(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        return self._send_and_get_responce(msg)

    def send_leave_room(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        return self._send_and_get_responce(msg)
