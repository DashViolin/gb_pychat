import binascii
import hashlib
import json
from contextlib import suppress

from sqlalchemy.exc import IntegrityError, NoResultFound

from config import CommonConf

from .server_model import Contact, History, Message, Session, User


class ServerStorage:
    def __init__(self) -> None:
        self.session = Session()
        self.set_all_users_inactive()

    def check_user_exists(self, username: str):
        try:
            self.session.query(User).filter_by(username=username).one()
            return True
        except NoResultFound:
            return False

    def user_auth(self, username: str, password: str):
        if self.check_user_exists:
            password = self.make_passwd_hash(username=username, password=password)
            db_password = self.get_user_password_hash(username=username)
            if password == db_password:
                return True
        return False

    def remove_user(self, username: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
        except NoResultFound:
            return False
        else:
            self.session.delete(user)
            self.session.commit()
            return True

    def make_passwd_hash(self, username: str, password: str):
        b_salt = username.encode(CommonConf.ENCODING)
        b_password = password.encode(CommonConf.ENCODING)
        pswd_hash = hashlib.pbkdf2_hmac("sha256", password=b_password, salt=b_salt, iterations=10000)
        return binascii.hexlify(pswd_hash).decode(CommonConf.ENCODING)

    def get_user_password_hash(self, username: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            return user.password
        except NoResultFound:
            return None

    def register_user(self, username, status=None, password=None, ip_address=None):
        if password:
            password = self.make_passwd_hash(username=username, password=password)
        try:
            user = self.session.query(User).filter_by(username=username).one()
        except NoResultFound:
            user = User(username=username, password=password, status=status)
        if ip_address:
            user.history.append(History(ip_address=ip_address))
        self.session.add(user)
        self.session.commit()

    def change_user_status(self, username: str, is_active: bool):
        user = self.session.query(User).filter_by(username=username).one()
        user.is_active = is_active
        self.session.add(user)
        self.session.commit()

    def get_active_users(self):
        query = self.session.query(User).filter_by(is_active=True).all()
        return [entry.username for entry in query]

    def get_users_history(self):
        query = self.session.query(History).all()
        return [(entry.user.username, entry.ip_address, entry.login_timestamp) for entry in query]

    def set_all_users_inactive(self):
        for user in self.get_active_users():
            self.change_user_status(user, is_active=False)

    def store_msg(self, user_from, user_to, msg: dict):
        user_from_query, user_to_query = self.register_contacts(user_from, user_to)
        contact_pair = (
            self.session.query(Contact).filter_by(user_id=user_from_query.id, contact_id=user_to_query.id).one()
        )
        msg_text = json.dumps(msg, ensure_ascii=False)
        contact_pair.messages.append(Message(text=msg_text))
        self.session.add(contact_pair)
        self.session.commit()

    def register_contacts(self, username, contact_name):
        with suppress(IntegrityError):
            self.register_user(username=username)
            self.register_user(username=contact_name)
        user_from_query = self.session.query(User).filter_by(username=username).one()
        user_to_query = self.session.query(User).filter_by(username=contact_name).one()
        user_from_query.contacts.append(user_to_query)
        self.session.add(user_from_query)
        self.session.commit()
        return user_from_query, user_to_query

    def get_user_messages(self, user_to):
        try:
            reciever = self.session.query(User).filter_by(username=user_to).one()
            contact_pairs = self.session.query(Contact).filter_by(contact_id=reciever.id).all()
        except NoResultFound:
            return []
        else:
            for pair in contact_pairs:
                try:
                    messages = self.session.query(Message).filter_by(contact_id=pair.id, is_delivered=False).all()
                    yield from ((entry.id, json.loads(entry.text)) for entry in messages)
                except NoResultFound:
                    continue

    def mark_msg_is_delivered(self, msg_id: int):
        self.session.query(Message).filter_by(id=msg_id).update({"is_delivered": True})
        self.session.commit()

    def get_user_contacts(self, username: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            contacts = self.session.query(Contact).filter_by(user_id=user.id, is_active=True).all()
        except NoResultFound:
            return []
        else:
            return [contact.contact.username for contact in contacts]

    def delete_contact(self, username: str, contact_name: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            contact = self.session.query(User).filter_by(username=contact_name).one()
            self.session.query(Contact).filter_by(user_id=user.id, contact_id=contact.id).update({"is_active": False})
            self.session.commit()
        except NoResultFound:
            pass

    def add_contact(self, username: str, contact_name: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            contact = self.session.query(User).filter_by(username=contact_name).one()
            self.session.query(Contact).filter_by(user_id=user.id, contact_id=contact.id).update({"is_active": True})
            self.session.commit()
        except NoResultFound:
            self.register_contacts(username=username, contact_name=contact_name)
