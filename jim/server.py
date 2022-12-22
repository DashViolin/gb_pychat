from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from select import select
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep

import config
from logger.server_log_config import main_logger

from .base import JIMBase
from .descriptors import PortDescriptor
from .errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from .schema import Actions, Keys
from .server_storage import ServerStorage


class JIMServer(JIMBase, ContextDecorator):
    port = PortDescriptor()

    def __init__(self, ip: str, port: int) -> None:
        super().__init__()
        self.ip = ip_address(ip)
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.connections = []
        self.active_clients = dict()
        self.storage = ServerStorage()

    def __str__(self):
        return "JIM_server_object"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        main_logger.info("Закрываю соединение...")
        self.close()

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
        active_users = self.storage.get_active_users()
        for user in active_users:
            client_conn = self.active_clients[user]
            for msg_id, msg in self.storage.get_user_messages(user_to=user):
                try:
                    self._send(msg=msg, client=client_conn)
                except (OSError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError):
                    self._disconnect_client(conn=client_conn, user=user)
                    break
                else:
                    self.storage.mark_msg_is_delivered(msg_id)

    def _cleanup_disconnected_users(self):
        disconnected_users = []
        for user, conn in self.active_clients.items():
            try:
                conn.getpeername()
            except OSError:
                disconnected_users.append((conn, user))
        for conn, user in disconnected_users:
            self._disconnect_client(conn, user)

    def _disconnect_client(self, conn: socket, user: str | None = None):
        if user:
            self.storage.change_user_status(username=user, is_active=False)
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
        self.sock.close()

    def _route_msg(self, client_conn: socket):
        response_code = HTTPStatus.OK
        response_descr = ""
        disconnect_client = False
        msg = self._recv(client_conn)
        if msg:
            try:
                self._validate_msg(msg)
                match msg.get(Keys.ACTION):
                    case Actions.PRESENCE | Actions.AUTH:
                        username = msg[Keys.USER][Keys.ACCOUNT_NAME]
                        if username not in self.active_clients:
                            self.active_clients[username] = client_conn
                            passwd = msg[Keys.USER].get(Keys.PASSWORD)
                            status = msg[Keys.USER].get(Keys.STATUS)
                            ip = client_conn.getpeername()[0]
                            self.storage.register_user(username=username, password=passwd, status=status, ip_address=ip)
                            self.storage.change_user_status(username=username, is_active=True)
                        else:
                            response_code = HTTPStatus.FORBIDDEN
                            response_descr = "Клиент с таким именем уже зарегистрирован на сервере"
                            disconnect_client = True
                    case Actions.MSG:
                        username = msg[Keys.FROM]
                        target_user = msg[Keys.TO]
                        self.storage.store_msg(user_from=username, user_to=target_user, msg=msg)
                    case Actions.CONTACTS:
                        username = msg[Keys.ACCOUNT_NAME]
                        contacts = self.storage.get_user_contacts(username=username)
                        response_descr = contacts
                    case Actions.ADD_CONTACT:
                        username = msg[Keys.ACCOUNT_NAME]
                        contact = msg[Keys.CONTACT]
                        self.storage.add_contact(username=username, contact_name=contact)
                    case Actions.DEL_CONTACT:
                        username = msg[Keys.ACCOUNT_NAME]
                        contact = msg[Keys.CONTACT]
                        self.storage.delete_contact(username=username, contact_name=contact)
                    case Actions.QUIT:
                        disconnect_client = True
                    case Actions.JOIN | Actions.LEAVE:
                        response_code = HTTPStatus.BAD_REQUEST
                    case _:
                        response_code = HTTPStatus.BAD_REQUEST

            except (NonDictInputError, IncorrectDataRecivedError) as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(f"Принято некорректное сообщение: {response_descr}")
            except ReqiuredFieldMissingError as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(f"Ошибка валидации сообщения: {response_descr}")
            except Exception as ex:
                response_code = HTTPStatus.INTERNAL_SERVER_ERROR
                response_descr = str(ex)
                main_logger.error(f"Непредвиденная ошибка: {response_descr}")
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

    def _make_response_msg(self, code: HTTPStatus, description: str | list = ""):
        description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        return msg
