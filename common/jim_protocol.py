import json
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket

from common import config


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


class __JIMBase:
    def __init__(self) -> None:
        self.encoding = config.Common.ENCODING
        self.package_length = config.Common.MAX_PACKAGE_LENGTH

    @abstractmethod
    def close():
        pass

    def _from_timestamp(self, timestamp: float | int) -> str:
        return datetime.fromtimestamp(timestamp).isoformat()

    def _dump_msg(self, msg: dict) -> bytes:
        timestamp = {Keys.TIME: datetime.now().timestamp()}
        msg.update(timestamp)
        return json.dumps(msg).encode(self.encoding)

    def _load_msg(self, data: bytes) -> dict:
        msg: dict = json.loads(data.decode(self.encoding))
        timestamp = msg.get(Keys.TIME, 0)
        msg.update({Keys.TIME: self._from_timestamp(timestamp)})
        return msg


class JIMServer(__JIMBase):
    def __init__(self, conn_params) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.conn_params = conn_params
        super().__init__()

    def listen(self):
        self.sock.bind(self.conn_params)
        self.sock.listen(config.Sever.MAX_CONNECTIONS)
        self.client, self.addr = self.sock.accept()
        print(f"Подключился клиент {':'.join(map(str, self.addr))}", end="\n\n")

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


class JIMClient(__JIMBase):
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
            Keys.ACTION: Actions.AUTHENTICATE,
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
            Keys.MESSAGE: message,
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
