import json
from collections import defaultdict
from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from select import select
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep

import config
from logger.server_log_config import main_logger

from .base import JIMBase
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from .schema import Actions, Keys


class PortDescriptor:
    def __init__(self, value: int = 7777):
        self.__set_port(value)

    def __set_port(self, value: int):
        if not 1023 < value < 65536:
            raise ValueError("Номер порта должен быть положительным числом в диапазоне [1024, 65535].")
        self._value = value

    def __get__(self, instance, instance_type):
        return self._value

    def __set__(self, instance, value):
        self.__set_port(value)

    def __delete__(self, instance):
        raise AttributeError("Невозможно удалить атрибут.")


class JIMServer(JIMBase, ContextDecorator):
    port = PortDescriptor()

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip_address(ip)
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.msg_queue_dump_file = config.ServerConf.MSG_DUMP_FILE
        self.connections = []
        self.active_clients = dict()
        self.messages_queue = self._load_messages()
        super().__init__()

    def __str__(self):
        return "JIM_server_object"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

    def _dump_messages(self):
        if self.messages_queue:
            with open(self.msg_queue_dump_file, "w", encoding=config.CommonConf.ENCODING) as dump:
                json.dump(self.messages_queue, dump, ensure_ascii=False, indent=2)
                main_logger.info(f"Сообщения сохранены в файл {self.msg_queue_dump_file}")

    def _load_messages(self) -> defaultdict:
        if self.msg_queue_dump_file.exists():
            with open(self.msg_queue_dump_file, "r", encoding=config.CommonConf.ENCODING) as dump:
                messages_queue = defaultdict(list, json.load(dump))
                main_logger.info(f"Сообщения загружены из файла {self.msg_queue_dump_file}")
                return messages_queue
        return defaultdict(list)

    def _listen(self):
        self.sock.bind((str(self.ip), self.port))
        self.sock.setblocking(False)
        self.sock.settimeout(0.2)
        self.sock.listen(config.ServerConf.MAX_CONNECTIONS)
        main_logger.info(f"Сервер запущен на {self.ip}:{self.port}.")

    def start_server(self):
        while True:
            try:
                self._listen()
                break
            except OSError:
                main_logger.info(f"Ожидается освобождение сокета {self.ip}:{self.port}...")
                sleep(1)
        self._mainloop()

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

    def _cleanup_disconnected_users(self):
        disconnected_users = []
        for user, conn in self.active_clients.items():
            try:
                conn.getpeername()
            except OSError:
                disconnected_users.append(user)
        for user in disconnected_users:
            self.active_clients.pop(user)

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

    def close(self):
        self._dump_messages()
        self.sock.close()

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

    def _recv(self, client) -> dict | None:
        msg = None
        try:
            raw_data = client.recv(self.package_length)
            msg = self._load_msg(raw_data)
        except (IncorrectDataRecivedError, OSError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError):
            self._disconnect_client(conn=client)
        finally:
            return msg

    def _send(self, msg, client):
        msg_raw_data = self._dump_msg(msg)
        client.send(msg_raw_data)

    def _make_probe_msg(self):
        msg = {Keys.ACTION: Actions.PROBE}
        return msg

    def _make_response_msg(self, code: HTTPStatus, description: str = ""):
        description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        return msg
