from http import HTTPStatus
from unittest import TestCase, mock

from common.jim_protocol.jim_base import Actions, Keys
from common.jim_protocol.jim_server import JIMServer


class BaseServerTestCase(TestCase):
    def setUp(self):
        self.mock_time = {Keys.TIME: 0}
        conn_params = ("127.0.0.1", 7777)
        self.server = JIMServer(conn_params)
        self.server.close()
        self.server.sock = mock.Mock()
        self.server.sock.listen.return_value = None
        self.server.sock.bind.return_value = None
        self.server.sock.accept.return_value = (mock.Mock(), ("192.168.1.1", 33333))
        self.server.listen()
        return super().setUp()


class TestJIMBase(BaseServerTestCase):
    def setUp(self):
        return super().setUp()

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

    def test_recv(self):
        client_presence = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: "user", Keys.STATUS: ""}}
        self.server.client.recv.return_value = self.server._dump_msg(client_presence)
        msg = self.server.recv()
        msg.update(self.mock_time)
        client_presence.update(self.mock_time)
        self.assertEqual(client_presence, msg)

    # def test_close(self): pass  # nothing to test

    # def test_send(self): pass  # nothing to test

    def test_make_probe_msg(self):
        probe_msg_orig = {Keys.ACTION: Actions.PROBE}
        probe_msg = self.server.make_probe_msg()
        self.assertEqual(probe_msg, probe_msg_orig)

    def test_make_response_msg_ok(self):
        response_orig = {
            Keys.RESPONSE: HTTPStatus.OK,
            Keys.ALERT: HTTPStatus.OK.phrase,
        }
        response_msg = self.server.make_response_msg(code=HTTPStatus.OK)
        self.assertEqual(response_msg, response_orig)

    def test_make_response_msg_403(self):
        response_orig = {
            Keys.RESPONSE: HTTPStatus.FORBIDDEN,
            Keys.ERROR: HTTPStatus.FORBIDDEN.phrase,
        }
        response_msg = self.server.make_response_msg(code=HTTPStatus.FORBIDDEN)
        self.assertEqual(response_msg, response_orig)

    def test_make_response_msg_error_with_descr(self):
        descr = "some_description"
        response_orig = {
            Keys.RESPONSE: HTTPStatus.INTERNAL_SERVER_ERROR,
            Keys.ERROR: descr,
        }
        response_msg = self.server.make_response_msg(code=HTTPStatus.INTERNAL_SERVER_ERROR, description=descr)
        self.assertEqual(response_msg, response_orig)
