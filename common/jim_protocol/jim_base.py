import json
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError

import config

from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError


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
    MSG = "message"
    RESPONSE = "response"
    ALERT = "alert"
    ERROR = "error"


@dataclass
class Actions:
    AUTH = "authenticate"
    PRESENCE = "presence"
    PROBE = "probe"
    QUIT = "quit"
    MSG = "msg"
    JOIN = "join"
    LEAVE = "leave"


@dataclass
class JIMValidationSchema:
    msg_keys = {
        Actions.AUTH: {Keys.ACTION, Keys.TIME, Keys.USER},
        Actions.PRESENCE: {Keys.ACTION, Keys.TIME, Keys.USER},
        Actions.PROBE: {Keys.ACTION, Keys.TIME},
        Actions.QUIT: {Keys.ACTION, Keys.TIME},
        Actions.MSG: {Keys.ACTION, Keys.TIME, Keys.FROM, Keys.TO, Keys.MSG, Keys.ENCODING},
        Actions.JOIN: {Keys.ACTION, Keys.TIME, Keys.ROOM},
        Actions.LEAVE: {Keys.ACTION, Keys.TIME, Keys.ROOM},
    }

    usr_keys = {Actions.AUTH: {Keys.ACCOUNT_NAME, Keys.PASSWORD}, Actions.PRESENCE: {Keys.ACCOUNT_NAME, Keys.STATUS}}

    resp_keys = {
        Keys.ALERT: {Keys.RESPONSE, Keys.ALERT, Keys.TIME},
        Keys.ERROR: {Keys.RESPONSE, Keys.ERROR, Keys.TIME},
    }


class JIMBase:
    def __init__(self) -> None:
        self.encoding = config.CommonConf.ENCODING
        self.package_length = config.CommonConf.MAX_PACKAGE_LENGTH
        self.schema = JIMValidationSchema()

    @abstractmethod
    def close():
        pass

    def _validate_keys(self, schema_keys: set, msg: dict):
        missing = schema_keys - msg.keys()
        if missing:
            raise ReqiuredFieldMissingError(missing_fields=missing)

    def validate_msg(self, msg: dict):
        if not isinstance(msg, dict):
            raise NonDictInputError()
        try:
            if action := msg.get(Keys.ACTION):
                self._validate_keys(self.schema.msg_keys[action], msg)
                if action in self.schema.usr_keys:
                    self._validate_keys(self.schema.usr_keys[action], msg[Keys.USER])
            elif response := msg[Keys.RESPONSE]:
                keys = self.schema.resp_keys[Keys.ERROR] if 400 <= response < 600 else self.schema.resp_keys[Keys.ALERT]
                self._validate_keys(keys, msg)
        except KeyError:
            raise IncorrectDataRecivedError()

    def _from_timestamp(self, timestamp: float | int) -> str:
        return datetime.fromtimestamp(timestamp).isoformat()

    def _dump_msg(self, msg: dict) -> bytes:
        timestamp = {Keys.TIME: datetime.now().timestamp()}
        msg.update(timestamp)
        return json.dumps(msg).encode(self.encoding)

    def _load_msg(self, data: bytes) -> dict:
        try:
            msg: dict = json.loads(data.decode(self.encoding))
            timestamp = msg.get(Keys.TIME, 0)
            msg.update({Keys.TIME: self._from_timestamp(timestamp)})
            return msg
        except JSONDecodeError:
            raise IncorrectDataRecivedError()
