from contextlib import ContextDecorator
from http import HTTPStatus
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from time import sleep

import config
from logger.client_log_config import call_logger, main_logger
from logger.decorator import log

from .base import Actions, JIMBase, Keys
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError


class JIMClient(JIMBase, ContextDecorator):
    @log(call_logger)
    def __init__(self, conn_params, username) -> None:
        self.conn_params = conn_params
        self.username = username
        self.sock = socket(AF_INET, SOCK_STREAM)
        super().__init__()

    def __str__(self):
        return f"JIM_client_object"

    @log(call_logger)
    def __enter__(self):
        return self

    @log(call_logger)
    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    @log(call_logger)
    def _connect(self):
        self.sock.connect(self.conn_params)
        presense = self._make_presence_msg()
        self._send(presense)
        response = self._recv()
        return response

    @log(call_logger)
    def close(self):
        self.sock.close()

    @log(call_logger)
    def run(self):
        while True:
            server_name = ":".join(map(str, self.conn_params))
            try:
                response = self._connect()
                self._validate_msg(response)
                main_logger.debug(f"Получен ответ от сервера: {response}")
                match response[Keys.RESPONSE]:
                    case HTTPStatus.OK:
                        main_logger.info(f"Успешно подключен к серверу {server_name} от имени {self.username}")
                        break
                    case HTTPStatus.FORBIDDEN:
                        main_logger.warning(f"Сервер {server_name} отказал в подключении: {response}")
                        raise KeyboardInterrupt
                    case _:
                        pass
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.info(
                    f"Не удалось подключиться от имени {self.username} к серверу {server_name} ({str(ex)})"
                )
                raise KeyboardInterrupt
            except ConnectionRefusedError as ex:
                main_logger.info(f"Пытаюсь подключиться как {self.username} к серверу {server_name}...")
                sleep(1)

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

    @log(call_logger)
    def _start_sender_loop(self):
        while True:
            try:
                username = str(input("Введите имя адресата: "))
                if username.strip():
                    msg_text = str(input(f"Введите текст (или '{config.CommonConf.EXIT_WORD}' для выхода): "))
                    if msg_text.strip() == config.CommonConf.EXIT_WORD:
                        quit = self._make_quit_msg()
                        self._send(quit)
                        self.close()
                        break
                    msg = self._make_msg(username, msg_text)
                    self._send(msg)
                    main_logger.debug(f"Отправлено сообщение: {msg}")
                else:
                    continue
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.error(ex)

    @log(call_logger)
    def _start_reciever_loop(self):
        while True:
            try:
                msg = self._recv()
                self._validate_msg(msg)
                self._process_msg(msg)
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.error(ex)
            except OSError:
                main_logger.info("Соединение разорвано.")
                break

    @log(call_logger)
    def _process_msg(self, msg):
        if msg.get(Keys.ACTION) == Actions.MSG:
            user = msg[Keys.FROM]
            text = msg[Keys.MSG]
            print(f"Сообщение от пользователя {user}: {text}")
            main_logger.debug(f"Получено сообщение: {msg}")
        elif msg.get(Keys.ACTION) == Actions.PROBE:
            main_logger.debug(f"Получено сообщение от сервера: {msg}")
        elif code := msg.get(Keys.RESPONSE):
            if code == HTTPStatus.OK:
                main_logger.debug(f"Получен ответ от сервера: {msg}")
            else:
                main_logger.error(f"Ошибка: {msg}")
        else:
            main_logger.error(f"Сообщение не распознано: {msg}")

    @log(call_logger)
    def _send(self, msg: dict):
        msg_raw_data = self._dump_msg(msg)
        self.sock.send(msg_raw_data)

    @log(call_logger)
    def _recv(self) -> dict:
        raw_resp_data = self.sock.recv(self.package_length)
        return self._load_msg(raw_resp_data)

    @log(call_logger)
    def _make_presence_msg(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        return msg

    @log(call_logger)
    def _make_authenticate_msg(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        return msg

    @log(call_logger)
    def _make_quit_msg(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        return msg

    @log(call_logger)
    def _make_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MSG: message,
            Keys.ENCODING: self.encoding,
        }
        return msg

    @log(call_logger)
    def _make_join_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        return msg

    @log(call_logger)
    def _make_leave_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        return msg
