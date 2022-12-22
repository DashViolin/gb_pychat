from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from time import sleep

import config
from logger.client_log_config import main_logger

from .base import JIMBase
from .client_storage import ClientStorage
from .descriptors import PortDescriptor
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError, ServerDisconnectError
from .schema import Actions, Keys


class JIMClient(JIMBase, ContextDecorator):
    port = PortDescriptor()

    def __init__(self, ip: str, port: int, username: str) -> None:
        super().__init__()
        self.ip = ip_address(ip)
        self.port = port
        self.server_name = f"{self.ip}:{self.port}"
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.username = username
        self.msg_factory = ClientMessages(self.username, self.encoding)
        self.storage = ClientStorage(self.username)
        self.status = self.storage.get_user_status(self.username)
        self.msg_queue = []

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
                presense = self.msg_factory.make_presence_msg(status=self.status)
                self._send(presense)
                response = self._recv()
                self._validate_msg(response)
                main_logger.debug(f"Получен ответ от сервера: {response}")
                match response[Keys.RESPONSE]:
                    case HTTPStatus.OK:
                        main_logger.info(f"Успешно подключен к серверу {self.server_name} от имени {self.username}")
                        return True
                    case HTTPStatus.FORBIDDEN:
                        main_logger.warning(f"Сервер {self.server_name} отказал в подключении: {response}")
                        raise KeyboardInterrupt
                    case _:
                        pass
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.info(
                    f"Не удалось подключиться от имени {self.username} к серверу {self.server_name} ({str(ex)})"
                )
                raise KeyboardInterrupt
            except ConnectionRefusedError as ex:
                main_logger.info(f"Пытаюсь подключиться как {self.username} к серверу {self.server_name}...")
                sleep(1)

    def _pull_contacts(self):
        contacts_msg = self.msg_factory.make_get_contacts_msg()
        self._send(contacts_msg)
        response = self._recv()
        self._validate_msg(response)
        main_logger.debug(f"Получен ответ от сервера: {response}")
        if response[Keys.RESPONSE] == HTTPStatus.ACCEPTED:
            contacts = response[Keys.ALERT]
            return contacts
        return []

    def close(self):
        self.sock.close()

    def run(self):
        connected = self._connect()
        if connected:
            contacts = self._pull_contacts()
            self.storage.update_contacts(contacts)

            receiver = Thread(target=self._start_reciever_loop)
            receiver.daemon = True
            receiver.start()

            sender = Thread(target=self._start_sender_loop)
            sender.daemon = True
            sender.start()

            while True:
                sleep(1)
                if receiver.is_alive() and sender.is_alive():
                    continue
                break

    def get_new_message(self):
        try:
            username = str(input("Введите имя адресата: "))
            if username.strip():
                msg_text = str(input(f"Введите текст (или '{config.CommonConf.EXIT_WORD}' для выхода): "))
                if msg_text.strip() == config.CommonConf.EXIT_WORD:
                    quit = self.msg_factory.make_quit_msg()
                    self._send(quit)
                    self.close()
                    raise KeyboardInterrupt
                msg = self.msg_factory.make_msg(username, msg_text)
                self.msg_queue.append(msg)
        except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
            main_logger.error(ex)

    def _start_sender_loop(self):
        while True:
            self.get_new_message()
            if self.msg_queue:
                try:
                    while self.msg_queue:
                        msg = self.msg_queue.pop()
                        self._send(msg)
                        main_logger.debug(f"Отправлено сообщение: {msg}")
                except Exception as ex:
                    main_logger.error(ex)

    def _start_reciever_loop(self):
        while True:
            try:
                msg = self._recv()
                try:
                    self._validate_msg(msg)
                except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                    main_logger.error(f"Принято некорректное сообщение: {msg} ({ex})")
                else:
                    self._process_incoming_msg(msg)
            except (OSError, ServerDisconnectError):
                main_logger.info("Соединение разорвано.")
                break

    def _process_incoming_msg(self, msg):
        if msg.get(Keys.ACTION) == Actions.MSG:
            user_from = msg[Keys.FROM]
            user_to = msg[Keys.TO]
            text = msg[Keys.MSG]
            timestamp = self._from_iso_to_datetime(msg[Keys.TIME])
            self.storage.store_msg(user_from=user_from, user_to=user_to, msg_text=text, timestamp=timestamp)
            main_logger.debug(f"Получено сообщение: {msg}")
        elif msg.get(Keys.ACTION) == Actions.PROBE:
            response = self.msg_factory.make_presence_msg(status=self.status)
            self.msg_queue.append(response)
            main_logger.debug(f"Получено сообщение от сервера: {msg}")
        elif code := msg.get(Keys.RESPONSE):
            if code == HTTPStatus.OK:
                main_logger.debug(f"Получен ответ от сервера: {msg}")
            else:
                main_logger.error(f"Ошибка: {msg}")
        else:
            main_logger.error(f"Сообщение не распознано: {msg}")

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


class ClientMessages:
    def __init__(self, username: str, encoding: str) -> None:
        self.username = username
        self.encoding = encoding

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

    def make_get_contacts_msg(self):
        msg = {Keys.ACTION: Actions.CONTACTS, Keys.ACCOUNT_NAME: self.username}
        return msg

    def make_add_contact_msg(self, contact: str):
        msg = {Keys.ACTION: Actions.ADD_CONTACT, Keys.ACCOUNT_NAME: self.username, Keys.CONTACT: contact}
        return msg

    def make_del_contact_msg(self, contact: str):
        msg = {Keys.ACTION: Actions.DEL_CONTACT, Keys.ACCOUNT_NAME: self.username, Keys.CONTACT: contact}
        return msg
