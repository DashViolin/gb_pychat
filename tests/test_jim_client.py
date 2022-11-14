from http import HTTPStatus
from unittest import TestCase, mock

from common import config
from common.jim_protocol.jim_base import Actions, Keys
from common.jim_protocol.jim_client import JIMClient


class TestJIMClient(TestCase):
    def setUp(self):
        self.encoding = config.Common.ENCODING
        self.username = "user"
        self.mock_time = {Keys.TIME: 0}
        self.mock_resp = {Keys.RESPONSE: HTTPStatus.OK.value, Keys.ALERT: HTTPStatus.OK.phrase}
        self.mock_resp.update(self.mock_time)
        conn_params = ("127.0.0.1", 7777)
        self.client = JIMClient(conn_params, self.username)
        self.client.close()
        self.client.sock = mock.Mock()
        self.client.sock.connect.return_value = None
        self.client.sock.send.return_value = None
        self.client.sock.recv.return_value = self.client._dump_msg(self.mock_resp.copy())
        return super().setUp()

    def test_connect(self):
        conn_is_ok, response = self.client.connect()
        response.update(self.mock_time)
        self.assertEqual((conn_is_ok, response), (True, self.mock_resp))

    def test_send_msg(self):
        msg = {"test_key": "test_msg"}
        response = self.client.send_msg(msg)
        response.update(self.mock_time)
        self.assertEqual(self.mock_resp, response)

    def test_make_presence_msg(self):
        status = "some_status"
        msg_orig = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        msg = self.client.make_presence_msg(status=status)
        self.assertEqual(msg, msg_orig)

    def test_make_authenticate_msg(self):
        passwd = "qwerty1234"
        msg_orig = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: passwd},
        }
        msg = self.client.make_authenticate_msg(password=passwd)
        self.assertEqual(msg, msg_orig)

    def test_make_quit_msg(self):
        msg_orig = {
            Keys.ACTION: Actions.QUIT,
        }
        msg = self.client.make_quit_msg()
        self.assertEqual(msg, msg_orig)

    def test_make_msg(self):
        target = "some_other_user"
        msg_text = "some_message"
        msg_orig = {
            Keys.ACTION: Actions.MSG,
            Keys.FROM: self.username,
            Keys.TO: target,
            Keys.MSG: msg_text,
            Keys.ENCODING: self.encoding,
        }
        msg = self.client.make_msg(user_or_room=target, message=msg_text)
        self.assertEqual(msg, msg_orig)

    def test_make_join_room_msg(self):
        room_name_right = "#room"
        msg_orig_right_room = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name_right}
        msg_right_room = self.client.make_join_room_msg(room_name_right)
        self.assertEqual(msg_right_room, msg_orig_right_room)

    def test_make_join_room_msg_with_wrong_room_name(self):
        room_name_right = "#room"
        room_name_wrong = "room"
        msg_orig = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name_right}
        msg = self.client.make_join_room_msg(room_name_wrong)
        self.assertEqual(msg, msg_orig)

    def test_make_leave_room_msg(self):
        room_name_right = "#room"
        msg_orig_right_room = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name_right}
        msg_right_room = self.client.make_leave_room_msg(room_name_right)
        self.assertEqual(msg_right_room, msg_orig_right_room)

    def test_make_leave_room_msg_with_wrong_room_name(self):
        room_name_right = "#room"
        room_name_wrong = "room"
        msg_orig = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name_right}
        msg = self.client.make_leave_room_msg(room_name_wrong)
        self.assertEqual(msg, msg_orig)
