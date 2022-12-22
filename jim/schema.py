from dataclasses import dataclass


@dataclass
class Keys:
    ACTION = "action"
    TIME = "time"
    USER = "user"
    CONTACT = "contact"
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
    CONTACTS = "get_contacts"
    ADD_CONTACT = "add_contact"
    DEL_CONTACT = "del_contact"
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
        Actions.CONTACTS: {Keys.ACTION, Keys.ACCOUNT_NAME, Keys.TIME},
        Actions.ADD_CONTACT: {Keys.ACTION, Keys.ACCOUNT_NAME, Keys.CONTACT, Keys.TIME},
        Actions.DEL_CONTACT: {Keys.ACTION, Keys.ACCOUNT_NAME, Keys.CONTACT, Keys.TIME},
    }

    usr_keys = {Actions.AUTH: {Keys.ACCOUNT_NAME, Keys.PASSWORD}, Actions.PRESENCE: {Keys.ACCOUNT_NAME, Keys.STATUS}}

    resp_keys = {
        Keys.ALERT: {Keys.RESPONSE, Keys.ALERT, Keys.TIME},
        Keys.ERROR: {Keys.RESPONSE, Keys.ERROR, Keys.TIME},
    }
