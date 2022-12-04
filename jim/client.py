from contextlib import ContextDecorator
from socket import AF_INET, SOCK_STREAM, socket

import config
from logger.client_log_config import call_logger, main_logger
from logger.decorator import log

from .base import Actions, JIMBase, Keys
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError


class JIMClient(JIMBase, ContextDecorator):
    @log(call_logger)
    def __init__(self, conn_params, mode, username) -> None:
        self.is_reader = mode
        self.conn_params = conn_params
        self.username = username
        self.sock = socket(AF_INET, SOCK_STREAM)
        super().__init__()

    def __str__(self):
        return "JIM_client_object"

    @log(call_logger)
    def __enter__(self):
        return self

    @log(call_logger)
    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    @log(call_logger)
    def connect(self):
        self.sock.connect(self.conn_params)
        presense = self.make_presence_msg()
        response = self.send(presense)
        return response

    @log(call_logger)
    def close(self):
        self.sock.close()

    @log(call_logger)
    def mainloop(self):
        if self.is_reader:
            self._start_reader_loop()
        else:
            self._start_writer_loop()

    @log(call_logger)
    def _start_writer_loop(self):
        while True:
            try:
                username = str(input("Введите имя адресата: "))
                msg_text = str(input(f"Введите текст (или '{config.CommonConf.EXIT_WORD}' для выхода): "))
                if msg_text.strip() == config.CommonConf.EXIT_WORD:
                    quit = self.make_quit_msg()
                    response = self.send(quit)
                    self.validate_msg(response)
                    main_logger.info(f"Получен ответ от сервера: {response}")
                    self.close()
                    break

                msg = self.make_msg(username, msg_text)
                response = self.send(msg)
                self.validate_msg(response)
                main_logger.info(f"Получен ответ от сервера: {response}")
            except (NonDictInputError, IncorrectDataRecivedError, ReqiuredFieldMissingError) as ex:
                main_logger.error(ex)

    @log(call_logger)
    def _start_reader_loop(self):
        while True:
            msg = self._recv()
            self.validate_msg(msg)
            main_logger.info(f"Получено сообщение: {msg}")

    @log(call_logger)
    def send(self, msg: dict):
        msg_raw_data = self._dump_msg(msg)
        self.sock.send(msg_raw_data)
        return self._recv()

    @log(call_logger)
    def _recv(self) -> dict:
        raw_resp_data = self.sock.recv(self.package_length)
        return self._load_msg(raw_resp_data)

    @log(call_logger)
    def make_presence_msg(self, status: str = ""):
        msg = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        return msg

    @log(call_logger)
    def make_authenticate_msg(self, password: str):
        msg = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: password},
        }
        return msg

    @log(call_logger)
    def make_quit_msg(self):
        msg = {
            Keys.ACTION: Actions.QUIT,
        }
        return msg

    @log(call_logger)
    def make_msg(self, user_or_room: str, message: str):
        msg = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: user_or_room,
            Keys.MSG: message,
            Keys.ENCODING: self.encoding,
        }
        return msg

    @log(call_logger)
    def make_join_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name}
        return msg

    @log(call_logger)
    def make_leave_room_msg(self, room_name: str):
        room_name = room_name if room_name.startswith("#") else f"#{room_name}"
        msg = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name}
        return msg
