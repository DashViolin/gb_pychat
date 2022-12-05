import json
from collections import defaultdict
from contextlib import ContextDecorator
from http import HTTPStatus
from select import select
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep

import config
from logger.decorator import log
from logger.server_log_config import call_logger, main_logger

from .base import Actions, JIMBase, Keys
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError


class JIMServer(JIMBase, ContextDecorator):
    @log(call_logger)
    def __init__(self, conn_params) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setblocking(False)
        self.msg_queue_dump_file = config.ServerConf.MSG_DUMP_FILE
        self.conn_params = conn_params
        self.sock_timeout = 0.2
        self.connections = []
        self.active_clients = dict()
        self.messages_queue = self._load_messages()
        super().__init__()

    def __str__(self):
        return "JIM_server_object"

    @log(call_logger)
    def __enter__(self):
        return self

    @log(call_logger)
    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    @log(call_logger)
    def _dump_messages(self):
        if self.messages_queue:
            with open(self.msg_queue_dump_file, "w", encoding=config.CommonConf.ENCODING) as dump:
                json.dump(self.messages_queue, dump, ensure_ascii=False, indent=2)
                main_logger.info(f"Сообщения сохранены в файл {self.msg_queue_dump_file}")

    @log(call_logger)
    def _load_messages(self) -> defaultdict:
        if self.msg_queue_dump_file.exists():
            with open(self.msg_queue_dump_file, "r", encoding=config.CommonConf.ENCODING) as dump:
                messages_queue = defaultdict(list, json.load(dump))
                main_logger.info(f"Сообщения загружены из файла {self.msg_queue_dump_file}")
                return messages_queue
        return defaultdict(list)

    @log(call_logger)
    def _listen(self):
        self.sock.bind(self.conn_params)
        main_logger.info(f"Сервер запущен на {':'.join(map(str, self.conn_params))}.")
        self.sock.settimeout(self.sock_timeout)
        self.sock.listen(config.ServerConf.MAX_CONNECTIONS)

    @log(call_logger)
    def start_server(self):
        while True:
            try:
                self._listen()
                break
            except OSError:
                main_logger.info(f"Ожидается освобождение сокета {':'.join(map(str, self.conn_params))}...")
                sleep(1)
        self._mainloop()

    @log(call_logger)
    def _mainloop(self):
        while True:
            try:
                conn, addr = self.sock.accept()
            except OSError:
                pass
            else:
                main_logger.info(f"Подключился клиент {':'.join(map(str, addr))}")
                self.connections.append(conn)
            finally:
                r_clients = []
                try:
                    if self.connections:
                        r_clients, _, _ = select(self.connections, self.connections, self.connections)
                except OSError:
                    pass

                for client in r_clients:
                    self._route_msg(client)

                self._cleanup_disconnected_users()
                self._process_messages_queue()

    @log(call_logger)
    def _process_messages_queue(self):
        active_users = set(self.messages_queue) & set(self.active_clients)
        for user in active_users:
            client = self.active_clients[user]
            while self.messages_queue[user]:
                msg = self.messages_queue[user].pop()
                try:
                    self._send(msg=msg, client=client)
                except (OSError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError):
                    self._disconnect_client(conn=client, user=user)
                    self.messages_queue[user].append(msg)
                    break

    @log(call_logger)
    def _cleanup_disconnected_users(self):
        disconnected_users = []
        for user, conn in self.active_clients.items():
            try:
                conn.getpeername()
            except OSError:
                disconnected_users.append(user)
        for user in disconnected_users:
            self.active_clients.pop(user)

    @log(call_logger)
    def _disconnect_client(self, conn: socket, user: str | None = None):
        if user:
            try:
                self.active_clients.pop(user)
            except KeyError:
                pass
        try:
            self.connections.remove(conn)
        except ValueError:
            pass
        conn.close()
        main_logger.info(f"Клиент отключился.")

    @log(call_logger)
    def close(self):
        self._dump_messages()
        self.sock.close()

    @log(call_logger)
    def _route_msg(self, client_conn: socket):
        response_code = HTTPStatus.OK
        response_descr = ""
        client_username = ""
        disconnect_client = False
        msg = self._recv(client_conn)
        if msg:
            try:
                self._validate_msg(msg)
                match msg.get(Keys.ACTION):
                    case Actions.PRESENCE | Actions.AUTH:
                        client_username = msg[Keys.USER][Keys.ACCOUNT_NAME]
                        if client_username not in self.active_clients:
                            self.active_clients[client_username] = client_conn
                        else:
                            response_code = HTTPStatus.FORBIDDEN
                            response_descr = "Клиент с таким именем уже зарегистрирован на сервере"
                            disconnect_client = True
                    case Actions.MSG:
                        target_user = msg[Keys.TO]
                        self.messages_queue[target_user].append(msg)
                    case Actions.QUIT:
                        disconnect_client = True
                    case Actions.JOIN | Actions.LEAVE:
                        response_code = HTTPStatus.BAD_REQUEST
                    case _:
                        response_code = HTTPStatus.BAD_REQUEST

            except (NonDictInputError, IncorrectDataRecivedError) as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(f"Принято некорректное сообщения от клиента {client_username}: {response_descr}")
            except ReqiuredFieldMissingError as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(
                    f"Ошибка валидации сообщения. Клиент: {client_username}, сообщение: {msg} ({response_descr})"
                )
            except Exception as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(f"Непредвиденная ошибка. Клиент: {client_username}, исключение: {response_descr}")
            finally:
                response = self._make_response_msg(code=response_code, description=response_descr)
                self._send(msg=response, client=client_conn)
                if disconnect_client:
                    self._disconnect_client(client_conn)

    @log(call_logger)
    def _recv(self, client) -> dict | None:
        msg = None
        try:
            raw_data = client.recv(self.package_length)
            msg = self._load_msg(raw_data)
        except (IncorrectDataRecivedError, OSError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError):
            self._disconnect_client(conn=client)
        finally:
            return msg

    @log(call_logger)
    def _send(self, msg, client):
        msg_raw_data = self._dump_msg(msg)
        client.send(msg_raw_data)

    @log(call_logger)
    def _make_probe_msg(self):
        msg = {Keys.ACTION: Actions.PROBE}
        return msg

    @log(call_logger)
    def _make_response_msg(self, code: HTTPStatus, description: str = ""):
        description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        return msg
