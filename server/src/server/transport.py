from contextlib import ContextDecorator
from http import HTTPStatus
from ipaddress import ip_address
from select import select
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep

from common.base import JIMBase
from common.decorators import login_required
from common.descriptors import PortDescriptor
from common.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from common.meta import JIMMeta
from common.schema import Actions, Keys
from server.config import ServerConf
from server.logger_conf import main_logger
from server.storage import ServerStorage


class JIMServer(JIMBase, ContextDecorator, metaclass=JIMMeta):
    """
    Класс ядра сервера, отвечает за роутинг сообщений и взаимодействие с клиентами и базой данных
    """

    port = PortDescriptor()

    def __init__(self, ip: str, port: int | str) -> None:
        super().__init__()
        self.ip = ip_address(ip)
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.connections = []
        self.active_clients = dict()
        self.storage = ServerStorage()
        self.is_running = False

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
        self.sock.listen(ServerConf.MAX_CONNECTIONS)
        main_logger.info(f"Сервер запущен на {self.ip}:{self.port}.")
        self.is_running = True

    def start_server(self):
        """Запускает сервер на прослушивание порта и обработку сообщений"""
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
            if not self.is_running:
                break
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
                    self._accept_message(client)
                self._cleanup_disconnected_users()

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
        self.connections = []
        self.active_clients = dict()
        self.is_running = False

    def _accept_message(self, client_conn: socket):
        response_code = HTTPStatus.OK
        response_descr = ""
        disconnect_client = False
        msg = self._recv(client_conn)
        if msg:
            try:
                self._validate_msg(msg)
                main_logger.debug(f"Принято сообщение: {msg}")
                if msg.get(Keys.ACTION) == Actions.AUTH:
                    response_code, response_descr, disconnect_client = self._register_user(msg, client_conn)
                else:
                    response_code, response_descr, disconnect_client = self._route_msg(msg, client_conn)
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
                main_logger.debug(f"Отправлен ответ: {response}")
                if disconnect_client:
                    self._disconnect_client(client_conn)

    def _register_user(self, msg: dict, client_conn: socket):
        username = msg[Keys.USER][Keys.ACCOUNT_NAME]
        if username in self.active_clients:
            response_code = HTTPStatus.FORBIDDEN
            response_descr = "Клиент с таким именем уже зарегистрирован на сервере"
            disconnect_client = True
        else:
            passwd = msg[Keys.USER].get(Keys.PASSWORD)
            ip = client_conn.getpeername()[0]
            if self.storage.check_user_auth(username=username, password=passwd):
                self.active_clients[username] = client_conn
                self.storage.register_user_login(username=username, ip_address=ip)
                response_code = HTTPStatus.OK
                response_descr = ""
                disconnect_client = False
            else:
                response_code = HTTPStatus.FORBIDDEN
                response_descr = "Неверное имя пользователя или пароль"
                disconnect_client = True
        return response_code, response_descr, disconnect_client

    @login_required
    def _route_msg(self, msg: dict, client_conn: socket):
        response_code = HTTPStatus.OK
        response_descr = ""
        disconnect_client = False
        match msg.get(Keys.ACTION):
            case Actions.PRESENCE:
                username = msg[Keys.USER][Keys.ACCOUNT_NAME]
                status = msg[Keys.USER].get(Keys.STATUS)
                self.storage.change_user_status(username=username, status=status, is_active=True)
            case Actions.MSG:
                username = msg[Keys.FROM]
                target_user = msg[Keys.TO]
                self.storage.add_contact(username=target_user, contact_name=username)
                if target_user in self.active_clients:
                    client_conn = self.active_clients[target_user]
                    self._send(msg=msg, client=client_conn)
                    main_logger.debug(f"Отправлено сообщение: {msg}")
                else:
                    response_code = HTTPStatus.NOT_FOUND
                    response_descr = "Пользователь не активен"
            case Actions.CONTACTS:
                username = msg[Keys.ACCOUNT_NAME]
                contacts = self.storage.get_user_contacts(username=username)
                response_code = HTTPStatus.ACCEPTED
                response_descr = contacts
            case Actions.ADD_CONTACT:
                username = msg[Keys.ACCOUNT_NAME]
                contact = msg[Keys.CONTACT]
                ok = self.storage.add_contact(username=username, contact_name=contact)
                if not ok:
                    response_code = HTTPStatus.NOT_FOUND
            case Actions.DEL_CONTACT:
                username = msg[Keys.ACCOUNT_NAME]
                contact = msg[Keys.CONTACT]
                ok = self.storage.delete_contact(username=username, contact_name=contact)
                if not ok:
                    response_code = HTTPStatus.NOT_FOUND
            case Actions.QUIT:
                disconnect_client = True
            case Actions.JOIN | Actions.LEAVE:
                response_code = HTTPStatus.BAD_REQUEST
            case _:
                response_code = HTTPStatus.BAD_REQUEST
        return response_code, response_descr, disconnect_client

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
        self._update_timestamp(msg=msg)
        return msg

    def _make_response_msg(self, code: HTTPStatus, description: str | list = ""):
        if not isinstance(description, list):
            description = description or code.phrase
        msg = {
            Keys.RESPONSE: code.value,
            Keys.ERROR if 400 <= code.value < 600 else Keys.ALERT: description,
        }
        self._update_timestamp(msg=msg)
        return msg
