from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from socket import AF_INET, SOCK_STREAM, socket
from threading import Lock, Thread
from time import sleep

from PyQt6 import QtCore

from logger.client_log_config import main_logger

from .base import JIMBase
from .client_messages import ClientMessages
from .client_storage import ClientStorage
from .descriptors import PortDescriptor
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError, ServerDisconnectError
from .schema import Actions, Keys


class SignalNotifier(QtCore.QObject):
    new_message = QtCore.pyqtSignal(str)
    connection_lost = QtCore.pyqtSignal()
    contacts_updated = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()


class JIMClient(JIMBase, ContextDecorator):
    port = PortDescriptor()
    socket_lock = Lock()

    def __init__(self, ip: str, port: int | str, username: str, password: str) -> None:
        super().__init__()
        self.connected = False
        self.ip = ip_address(ip)
        self.port = port
        self.server_name = f"{self.ip}:{self.port}"
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.username = username
        self.password = password
        self.msg_factory = ClientMessages(self.username, self.encoding)
        self.storage = ClientStorage(self.username)
        self.notifier = SignalNotifier()
        self.status = self.storage.get_user_status(self.username)

    def __str__(self):
        return f"JIM_client_object"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    def _connect(self):
        while True:
            try:
                self.sock.connect((str(self.ip), self.port))
                self.connected = True
                break
            except ConnectionRefusedError as ex:
                main_logger.info(f"Пытаюсь подключиться как {self.username} к серверу {self.server_name}...")
                sleep(1)
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.info(
                    f"Не удалось подключиться от имени {self.username} к серверу {self.server_name} ({str(ex)})"
                )
                break

    def close(self):
        self.sock.close()

    def run(self):
        if self.connected:
            self.sync_contacts()
            receiver = Thread(target=self._start_reciever_loop)
            receiver.daemon = True
            receiver.start()
            while True:
                sleep(1)
                if receiver.is_alive():
                    continue
                break

    def authenticate(self):
        self._connect()
        if self.connected:
            msg = self.msg_factory.make_authenticate_msg(password=self.password)
            resp = self._send_data(msg, return_response=True)
            if resp.get(Keys.RESPONSE) == HTTPStatus.OK:  # type: ignore
                main_logger.info(f"Успешно подключен к серверу {self.server_name} от имени {self.username}")
                self.send_presence(status=self.status)
                return True, resp
            return False, resp
        return False, dict()

    def sync_contacts(self):
        msg = self.msg_factory.make_get_contacts_msg()
        resp = self._send_data(msg, return_response=True)
        if resp[Keys.RESPONSE] == HTTPStatus.ACCEPTED:  # type: ignore
            main_logger.debug(f"Принят ответ: {resp}")
            contacts = resp.get(Keys.ALERT)  # type: ignore
            if contacts:
                self.storage.update_contacts(contacts)  # type: ignore
                self.notifier.contacts_updated.emit()
        else:
            main_logger.warning(f"Принят ответ: {resp}")

    def send_presence(self, status: str):
        msg = self.msg_factory.make_presence_msg(status=status)
        self._send_data(msg)

    def send_msg(self, contact: str, msg_text: str):
        msg = self.msg_factory.make_msg(user_or_room=contact, message=msg_text)
        timestamp = self._from_iso_to_datetime(msg[Keys.TIME])
        self._send_data(msg)
        self.storage.store_msg(user_from=self.username, user_to=contact, msg_text=msg_text, timestamp=timestamp)

    def add_contact(self, contact_name):
        msg = self.msg_factory.make_add_contact_msg(contact=contact_name)
        resp = self._send_data(msg, return_response=True)
        if resp and resp.get(Keys.RESPONSE) == HTTPStatus.OK:
            self.storage.add_contact(contact=contact_name)
            return True
        return False

    def delete_contact(self, contact_name):
        msg = self.msg_factory.make_del_contact_msg(contact=contact_name)
        self._send_data(msg)
        self.storage.del_contact(contact=contact_name)

    def set_user_status(self, status: str):
        self.storage.set_user_status(username=self.username, status=status)

    def _start_reciever_loop(self):
        while True:
            try:
                msg = self._recv()
                try:
                    self._validate_msg(msg)
                except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                    main_logger.error(f"Принято некорректное сообщение: {msg} ({ex})")
                else:
                    main_logger.info(f"Принято сообщение: {msg}")
                    self._process_incoming_msg(msg)
            except (OSError, ServerDisconnectError):
                main_logger.info("Соединение разорвано.")
                self.notifier.connection_lost.emit()
                break

    def _process_incoming_msg(self, msg):
        if msg.get(Keys.ACTION) == Actions.MSG:
            user_from = msg[Keys.FROM]
            user_to = msg[Keys.TO]
            text = msg[Keys.MSG]
            timestamp = self._from_iso_to_datetime(msg[Keys.TIME])
            self.storage.store_msg(user_from=user_from, user_to=user_to, msg_text=text, timestamp=timestamp)
            self.notifier.new_message.emit(user_from)
            main_logger.debug(f"Получено сообщение: {msg}")
        elif msg.get(Keys.ACTION) == Actions.PROBE:
            self.send_presence(status=self.status)
            main_logger.debug(f"Получено сообщение от сервера: {msg}")
        else:
            main_logger.error(f"Сообщение не распознано: {msg}")

    def _send_data(self, msg_data: dict, return_response: bool = False):
        with self.socket_lock:
            self._send(msg_data)
            main_logger.debug(f"Отправлено сообщение: {msg_data}")
            resp = self._recv()
        if not return_response:
            if resp.get(Keys.RESPONSE) == HTTPStatus.OK:
                main_logger.debug(f"Принят ответ: {resp}")
            else:
                main_logger.warning(f"Что-то не так: {resp}")
        else:
            return resp

    def _send(self, msg: dict):
        msg_raw_data = self._dump_msg(msg)
        self.sock.send(msg_raw_data)

    def _recv(self) -> dict:
        raw_resp_data = self.sock.recv(self.package_length)
        if not raw_resp_data:
            raise ServerDisconnectError()
        return self._load_msg(raw_resp_data)

    def _update_status(self, new_status: str):
        self.storage.set_user_status(username=self.username, status=new_status)
        self.status = self.storage.get_user_status(username=self.username)
