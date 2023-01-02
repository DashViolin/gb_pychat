import os
from copy import deepcopy
from http import HTTPStatus
from unittest import TestCase, mock

from config import ClientConf
from jim.client import JIMClient
from jim.schema import Actions, Keys


class TestJIMClient(TestCase):
    def setUp(self):
        self.encoding = ClientConf.ENCODING
        self.username = "some_testing_username"
        self.mock_time = {Keys.TIME: 0}
        self.mock_resp = {Keys.RESPONSE: HTTPStatus.OK.value, Keys.ALERT: HTTPStatus.OK.phrase}
        self.mock_resp.update(self.mock_time)
        self.ip = "127.0.0.1"
        self.port = 7777
        self.client = JIMClient(ip=self.ip, port=self.port, username=self.username, password="")
        self.client.close()
        self.client.sock = mock.Mock()
        self.client.sock.connect.return_value = None
        self.client.sock.send.return_value = None
        self.client.sock.recv.return_value = self.client._dump_msg(self.mock_resp.copy())
        return super().setUp()

    def tearDown(self) -> None:
        if self.client.storage.db_path.exists():
            os.remove(self.client.storage.db_path)
        return super().tearDown()

    def test_recv(self):
        resp_orig = deepcopy(self.mock_resp)
        resp_orig.update(self.mock_time)
        resp = self.client._recv()
        resp.update(self.mock_time)
        self.assertEqual(resp, resp_orig)

    def test_make_presence_msg(self):
        status = "some_status"
        msg_orig = {Keys.ACTION: Actions.PRESENCE, Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.STATUS: status}}
        msg = self.client.msg_factory.make_presence_msg(status=status)
        msg_orig.update(self.mock_time)
        msg.update(self.mock_time)
        self.assertEqual(msg, msg_orig)

    def test_make_authenticate_msg(self):
        passwd = "qwerty1234"
        msg_orig = {
            Keys.ACTION: Actions.AUTH,
            Keys.USER: {Keys.ACCOUNT_NAME: self.username, Keys.PASSWORD: passwd},
        }
        msg = self.client.msg_factory.make_authenticate_msg(password=passwd)
        msg_orig.update(self.mock_time)
        msg.update(self.mock_time)
        self.assertEqual(msg, msg_orig)

    def test_make_quit_msg(self):
        msg_orig = {
            Keys.ACTION: Actions.QUIT,
        }
        msg = self.client.msg_factory.make_quit_msg()
        msg_orig.update(self.mock_time)  # type: ignore
        msg.update(self.mock_time)  # type: ignore
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
        msg = self.client.msg_factory.make_msg(user_or_room=target, message=msg_text)
        msg_orig.update(self.mock_time)  # type: ignore
        msg.update(self.mock_time)  # type: ignore
        self.assertEqual(msg, msg_orig)

    def test_make_join_room_msg(self):
        room_name_right = "#room"
        msg_orig_right_room = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name_right}
        msg_right_room = self.client.msg_factory.make_join_room_msg(room_name_right)
        msg_orig_right_room.update(self.mock_time)  # type: ignore
        msg_right_room.update(self.mock_time)  # type: ignore
        self.assertEqual(msg_right_room, msg_orig_right_room)

    def test_make_join_room_msg_with_wrong_room_name(self):
        room_name_right = "#room"
        room_name_wrong = "room"
        msg_orig = {Keys.ACTION: Actions.JOIN, Keys.ROOM: room_name_right}
        msg = self.client.msg_factory.make_join_room_msg(room_name_wrong)
        msg_orig.update(self.mock_time)  # type: ignore
        msg.update(self.mock_time)  # type: ignore
        self.assertEqual(msg, msg_orig)

    def test_make_leave_room_msg(self):
        room_name_right = "#room"
        msg_orig_right_room = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name_right}
        msg_right_room = self.client.msg_factory.make_leave_room_msg(room_name_right)
        msg_orig_right_room.update(self.mock_time)  # type: ignore
        msg_right_room.update(self.mock_time)  # type: ignore
        self.assertEqual(msg_right_room, msg_orig_right_room)

    def test_make_leave_room_msg_with_wrong_room_name(self):
        room_name_right = "#room"
        room_name_wrong = "room"
        msg_orig = {Keys.ACTION: Actions.LEAVE, Keys.ROOM: room_name_right}
        msg = self.client.msg_factory.make_leave_room_msg(room_name_wrong)
        msg_orig.update(self.mock_time)  # type: ignore
        msg.update(self.mock_time)  # type: ignore
        self.assertEqual(msg, msg_orig)
