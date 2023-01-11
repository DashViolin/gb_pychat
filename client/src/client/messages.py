from datetime import datetime

from common.schema import Actions, Keys


class ClientMessages:
    """
    Класс для генерации валидных сообщений клиента по протоколу JIM
    """

    def __init__(self, username: str, encoding: str) -> None:
        self.username = username
        self.encoding = encoding

    def _update_timestamp(self, msg: dict):
        timestamp = {Keys.TIME: datetime.now().isoformat()}
        msg.update(timestamp)

    def make_presence_msg(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        self._update_timestamp(msg=msg)
        return msg

    def make_authenticate_msg(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        self._update_timestamp(msg=msg)
        return msg

    def make_quit_msg(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        self._update_timestamp(msg=msg)
        return msg

    def make_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MSG: message,
            Keys.ENCODING: self.encoding,
        }
        self._update_timestamp(msg=msg)
        return msg

    def make_join_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        self._update_timestamp(msg=msg)
        return msg

    def make_leave_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        self._update_timestamp(msg=msg)
        return msg

    def make_get_contacts_msg(self):
        msg = {Keys.ACTION: Actions.CONTACTS, Keys.ACCOUNT_NAME: self.username}
        self._update_timestamp(msg=msg)
        return msg

    def make_add_contact_msg(self, contact: str):
        msg = {Keys.ACTION: Actions.ADD_CONTACT, Keys.ACCOUNT_NAME: self.username, Keys.CONTACT: contact}
        self._update_timestamp(msg=msg)
        return msg

    def make_del_contact_msg(self, contact: str):
        msg = {Keys.ACTION: Actions.DEL_CONTACT, Keys.ACCOUNT_NAME: self.username, Keys.CONTACT: contact}
        self._update_timestamp(msg=msg)
        return msg
