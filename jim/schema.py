from dataclasses import dataclass


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
