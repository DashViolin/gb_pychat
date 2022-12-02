import os
import pathlib
from collections import defaultdict
from copy import deepcopy
from http import HTTPStatus
from unittest import TestCase, mock

from jim.base import Actions, Keys
from jim.errors import IncorrectDataRecivedError, NonDictInputError, ReqiuredFieldMissingError
from jim.server import JIMServer


class BaseServerTestCase(TestCase):
    def setUp(self):
        def make_client(ret_msg: dict):
            client = mock.Mock()
            client.close.return_value = None
            client.send.return_value = None
            client.getpeername.return_value = "mock_peer_name"
            client.recv.return_value = self.server._dump_msg(ret_msg)
            return client

        self.mock_time = {Keys.TIME: 0}
        conn_params = ("127.0.0.1", 7777)
        self.msg_queue_dump_file = pathlib.Path().resolve() / "tmp_dump_file.json"
        self.server = JIMServer(conn_params)
        self.server.close()
        self.server.msg_queue_dump_file = self.msg_queue_dump_file
        self.server.sock = mock.Mock()
        self.server.sock.listen.return_value = None
        self.server.sock.bind.return_value = None
        self.server.sock.accept.return_value = (mock.Mock(), ("192.168.1.1", 33333))
        self.server.listen()

        self.mock_presense = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: "user", Keys.STATUS: ""}}

        self.client1 = make_client(self.mock_presense)
        self.client2 = make_client({})
        self.users = ["user1", "user2"]
        self.connections = [
            self.client1,
            self.client2,
        ]
        self.mock_active_clients = {
            self.users[0]: self.client1,
            self.users[1]: self.client2,
        }
        self.mock_messages_queue = defaultdict(
            list,
            {
                user: [
                    {"field1": "message"},
                    {"field2": "message"},
                ]
                for user in self.mock_active_clients.keys()
            },
        )
        return super().setUp()

    def tearDown(self) -> None:
        if self.msg_queue_dump_file.exists():
            os.remove(self.msg_queue_dump_file)
        return super().tearDown()


class TestJIMBase(BaseServerTestCase):
    def setUp(self):
        return super().setUp()

    def test_validate_msg_ok(self):
        result = True
        try:
            self.server.validate_msg(self.mock_presense)
        except Exception:
            result = False
        finally:
            self.assertTrue(result)

    def test_validate_msg_non_dict(self):
        arg = [1, 2, 3]
        self.assertRaises(NonDictInputError, self.server.validate_msg, arg)

    def test_validate_msg_incorrect_data_error(self):
        arg = deepcopy(self.mock_presense)
        arg.pop(Keys.ACTION)
        self.assertRaises(IncorrectDataRecivedError, self.server.validate_msg, arg)

    def test_validate_msg_missing_key_error(self):
        arg = deepcopy(self.mock_presense)
        arg.pop(Keys.TIME)
        self.assertRaises(ReqiuredFieldMissingError, self.server.validate_msg, arg)

    def test_from_timestamp(self):
        iso_time_orig = "1970-01-01T03:00:00"
        iso_time = self.server._from_timestamp(0)
        self.assertEqual(iso_time, iso_time_orig)

    def test_dump_load_msg(self):
        orig_msg = {"some_key": "some_value"}
        result = self.server._load_msg(self.server._dump_msg(orig_msg))
        orig_msg.update(**self.mock_time)
        result.update(self.mock_time)
        self.assertEqual(orig_msg, result)


class TestJIMServer(BaseServerTestCase):
    def setUp(self):
        return super().setUp()

    def test_disconnect_client(self):
        user = self.users[0]
        conn = self.mock_active_clients[user]
        active_clients_result = self.mock_active_clients.copy()
        active_clients_result.pop(user)
        connections_result = self.connections.copy()
        connections_result.remove(conn)
        self.server.active_clients = self.mock_active_clients.copy()
        self.server.connections = self.connections.copy()
        self.server._disconnect_client(user=user, conn=conn)
        self.assertEqual(self.server.active_clients, active_clients_result)
        self.assertEqual(self.server.connections, connections_result)

    def test_cleanup_disconnected_users(self):
        disconnected_user = self.users[-1]
        active_clients = deepcopy(self.mock_active_clients)
        self.server.active_clients = active_clients.copy()
        active_clients.pop(disconnected_user)
        with mock.patch.object(
            self.server.active_clients[disconnected_user], "getpeername", mock.MagicMock(side_effect=OSError)
        ):
            self.server._cleanup_disconnected_users()
        self.assertEqual(self.server.active_clients, active_clients)

    def test_process_messages_queue(self):
        self.server.messages_queue = deepcopy(self.mock_messages_queue)
        self.server.active_clients = deepcopy(self.mock_active_clients)
        self.server._process_messages_queue()
        for user in self.server.messages_queue:
            self.assertEqual(self.server.messages_queue[user], [])

    def test_dump_and_load_messages(self):
        self.server.messages_queue = deepcopy(self.mock_messages_queue)
        self.server.dump_messages()
        self.server.load_messages()
        self.assertEqual(self.server.messages_queue, self.mock_messages_queue)

    def test_recv_presense(self):
        msg = self.server._recv(self.client1)
        if msg:
            msg.update(self.mock_time)
            client_presence = deepcopy(self.mock_presense)
            client_presence.update(self.mock_time)
            self.assertEqual(client_presence, msg)
        else:
            self.assertEqual(None, msg)

    def test_recv_none(self):
        self.client1.recv.return_value = b""
        msg = self.server._recv(self.client1)
        if msg:
            msg.update(self.mock_time)
            client_presence = deepcopy(self.mock_presense)
            client_presence.update(self.mock_time)
            self.assertEqual(client_presence, msg)
        else:
            self.assertEqual(None, msg)

    def test_make_probe_msg(self):
        probe_msg_orig = {Keys.ACTION: Actions.PROBE}
        probe_msg = self.server._make_probe_msg()
        self.assertEqual(probe_msg, probe_msg_orig)

    def test_make_response_msg_ok(self):
        response_orig = {
            Keys.RESPONSE: HTTPStatus.OK,
            Keys.ALERT: HTTPStatus.OK.phrase,
        }
        response_msg = self.server._make_response_msg(code=HTTPStatus.OK)
        self.assertEqual(response_msg, response_orig)

    def test_make_response_msg_403(self):
        response_orig = {
            Keys.RESPONSE: HTTPStatus.FORBIDDEN,
            Keys.ERROR: HTTPStatus.FORBIDDEN.phrase,
        }
        response_msg = self.server._make_response_msg(code=HTTPStatus.FORBIDDEN)
        self.assertEqual(response_msg, response_orig)

    def test_make_response_msg_error_with_descr(self):
        descr = "some_description"
        response_orig = {
            Keys.RESPONSE: HTTPStatus.INTERNAL_SERVER_ERROR,
            Keys.ERROR: descr,
        }
        response_msg = self.server._make_response_msg(code=HTTPStatus.INTERNAL_SERVER_ERROR, description=descr)
        self.assertEqual(response_msg, response_orig)
