import json
from abc import abstractmethod
from datetime import datetime
from json import JSONDecodeError

from .config import CommonConf
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from .schema import JIMValidationSchema, Keys


class JIMBase:
    """
    Базовый класс для классов сервера и клиента транспортных модулей,
    содержит общий функционал валидации и сериализации сообщений
    """

    def __init__(self) -> None:
        self.encoding = CommonConf.ENCODING
        self.package_length = CommonConf.MAX_PACKAGE_LENGTH
        self.schema = JIMValidationSchema()

    @abstractmethod
    def close():
        pass

    def _validate_keys(self, schema_keys: set, msg: dict):
        missing = schema_keys - set(msg.keys())
        if missing:
            raise ReqiuredFieldMissingError(missing_fields=missing)

    def _validate_msg(self, msg: dict):
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

    def _from_timestamp_to_iso(self, timestamp: float | int) -> str:
        return datetime.fromtimestamp(timestamp).isoformat()

    def _from_iso_to_datetime(self, iso_timestamp: str) -> datetime:
        return datetime.fromisoformat(iso_timestamp)

    def _update_timestamp(self, msg: dict):
        timestamp = {Keys.TIME: datetime.now().isoformat()}
        msg.update(timestamp)

    def _dump_msg(self, msg: dict) -> bytes:
        timestamp = {Keys.TIME: datetime.now().timestamp()}
        msg.update(timestamp)
        return json.dumps(msg).encode(self.encoding)

    def _load_msg(self, data: bytes) -> dict:
        try:
            msg: dict = json.loads(data.decode(self.encoding))
            timestamp = msg.get(Keys.TIME, 0)
            msg.update({Keys.TIME: self._from_timestamp_to_iso(timestamp)})
            return msg
        except JSONDecodeError:
            raise IncorrectDataRecivedError()
