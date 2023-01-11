from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from socket import AF_INET, SOCK_STREAM, socket
from threading import Lock, Thread
from time import sleep

from common.base import JIMBase
from common.descriptors import PortDescriptor
from common.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError, ServerDisconnectError
from common.schema import Actions, Keys
from PyQt6 import QtCore

from client.logger_conf import main_logger
from client.messages import ClientMessages
from client.storage import ClientStorage

socket_lock = Lock()


class SignalNotifier(QtCore.QObject):
    """
    Класс-генератор сигналов PyQt для взаимодействия с графическим интерфейсом
    """

    new_message = QtCore.pyqtSignal(str)
    connection_lost = QtCore.pyqtSignal()
    contacts_updated = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()


class JIMClient(Thread, JIMBase, ContextDecorator):
    """
    Класс ядра клиента, отвечает за прием и передачу сообщений, а также взаимодействие с базой данных
    """

    port = PortDescriptor()

    def __init__(self, ip: str, port: int | str, username: str, password: str) -> None:
        Thread.__init__(self)
        JIMBase.__init__(self)
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
        self.status = ""

    def __str__(self):
        return f"JIM_client_object"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _connect(self):
        while True:
            try:
                if not self.sock:
                    self.sock = socket(AF_INET, SOCK_STREAM)
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
        main_logger.info("Закрываю соединение...")
        self.sock.close()

    def authenticate(self):
        """Запускает подключение и аутентификацию клиента на сервере"""
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

    def run(self):
        """Запускает синхронизацию контактов и фоновый поток обработки сообщений после подключения и аутентификации"""
        if self.connected:
            self.sync_contacts()
            receiver = Thread(target=self._start_reciever_loop)
            receiver.daemon = True
            receiver.start()
            while True:
                if not self.connected:
                    break
                sleep(1)
                if receiver.is_alive():
                    continue
                break

    def sync_contacts(self):
        msg = self.msg_factory.make_get_contacts_msg()
        resp = self._send_data(msg, return_response=True)
        if resp[Keys.RESPONSE] == HTTPStatus.ACCEPTED:  # type: ignore
            contacts = resp.get(Keys.ALERT)  # type: ignore
            self.storage.update_contacts(contacts)  # type: ignore
            self.notifier.contacts_updated.emit()

    def send_presence(self, status: str):
        msg = self.msg_factory.make_presence_msg(status=status)
        self._send_data(msg)

    def send_msg(self, contact: str, msg_text: str, store_msg: bool = True):
        msg = self.msg_factory.make_msg(user_or_room=contact, message=msg_text)
        timestamp = self._from_iso_to_datetime(msg[Keys.TIME])
        resp = self._send_data(msg, return_response=True)
        is_delivered = False
        if resp and resp.get(Keys.RESPONSE) == HTTPStatus.OK:
            is_delivered = True
        if store_msg:
            self.storage.store_msg(
                contact=contact, msg_text=msg_text, timestamp=timestamp, is_incoming=False, is_delivered=is_delivered
            )
        return is_delivered

    def resend_not_delivered(self, contact: str):
        messages = self.storage.get_not_delivered_msgs(contact=contact)
        for msg_id, msg_text in messages:
            is_delivered = self.send_msg(contact=contact, msg_text=msg_text, store_msg=False)
            if is_delivered:
                self.storage.mark_msg_delivered(msg_id=msg_id)
            sleep(0.1)

    def add_contact(self, contact_name):
        msg = self.msg_factory.make_add_contact_msg(contact=contact_name)
        resp = self._send_data(msg, return_response=True)
        if resp and resp.get(Keys.RESPONSE) == HTTPStatus.OK:
            self.storage.add_contact(contact=contact_name)
            return True
        return False

    def delete_contact(self, contact_name):
        msg = self.msg_factory.make_del_contact_msg(contact=contact_name)
        resp = self._send_data(msg, return_response=True)
        if resp and resp.get(Keys.RESPONSE) == HTTPStatus.OK:
            self.storage.del_contact(contact=contact_name)
            return True
        return False

    def _start_reciever_loop(self):
        while True:
            if not self.connected:
                break
            sleep(1)
            with socket_lock:
                self.sock.settimeout(0.5)
                try:
                    msg = self._recv()
                    try:
                        self._validate_msg(msg)
                    except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                        main_logger.error(f"Принято некорректное сообщение: {msg} ({ex})")
                    else:
                        main_logger.info(f"Принято сообщение: {msg}")
                        self._process_server_msg(msg)
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, ServerDisconnectError):
                    main_logger.info("Потеряно соединение с сервером.")
                    self.notifier.connection_lost.emit()
                    self.connected = False
                    break
                except OSError as ex:
                    if ex.errno:
                        main_logger.info("Потеряно соединение с сервером.")
                        self.notifier.connection_lost.emit()
                        self.connected = False
                        break
                finally:
                    self.sock.settimeout(5)

    def _process_server_msg(self, msg):
        if msg.get(Keys.ACTION) == Actions.MSG:
            user_from = msg[Keys.FROM]
            if not self.storage.check_contact(contact=user_from):
                self.storage.add_contact(contact=user_from)
            text = msg[Keys.MSG]
            timestamp = self._from_iso_to_datetime(msg[Keys.TIME])
            self.storage.store_msg(contact=user_from, msg_text=text, is_incoming=True, timestamp=timestamp)
            self.notifier.new_message.emit(user_from)
            main_logger.debug(f"Получено сообщение: {msg}")
        elif msg.get(Keys.ACTION) == Actions.PROBE:
            self.send_presence(status=self.status)
            main_logger.debug(f"Получено сообщение от сервера: {msg}")
        else:
            main_logger.error(f"Сообщение не распознано: {msg}")

    def _send_data(self, msg_data: dict, return_response: bool = False):
        with socket_lock:
            msg_raw_data = self._dump_msg(msg_data)
            self.sock.send(msg_raw_data)
            resp = self._recv()
        main_logger.debug(f"Отправлено сообщение: {msg_data}")
        main_logger.debug(f"Принят ответ: {resp}")
        if return_response:
            return resp

    def _recv(self) -> dict:
        raw_resp_data = self.sock.recv(self.package_length)
        if not raw_resp_data:
            raise ServerDisconnectError()
        return self._load_msg(raw_resp_data)
