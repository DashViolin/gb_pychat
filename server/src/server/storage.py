import binascii
import hashlib

from sqlalchemy.exc import NoResultFound

from server.config import ServerConf
from server.model import Contact, History, User, init_db


class ServerStorage:
    """
    Класс-обертка над ORM для взаимодействия сервера с базой данных
    """

    def __init__(self) -> None:
        self.session = init_db()
        self.set_all_users_inactive()

    def check_user_exists(self, username: str):
        try:
            self.session.query(User).filter_by(username=username).one()
            return True
        except NoResultFound:
            return False

    def check_user_auth(self, username: str, password: str):
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
        b_salt = username.encode(ServerConf.ENCODING)
        b_password = password.encode(ServerConf.ENCODING)
        pswd_hash = hashlib.pbkdf2_hmac("sha256", password=b_password, salt=b_salt, iterations=10000)
        return binascii.hexlify(pswd_hash).decode(ServerConf.ENCODING)

    def get_user_password_hash(self, username: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            return user.password
        except NoResultFound:
            return None

    def register_user_login(self, username, ip_address):
        history = History(username=username, ip_address=ip_address)
        self.session.add(history)
        self.session.commit()

    def add_user(self, username, password):
        password = self.make_passwd_hash(username=username, password=password)
        user = User(username=username, password=password)
        self.session.add(user)
        self.session.commit()

    def change_user_status(self, username: str, is_active: bool, status: str = ""):
        user = self.session.query(User).filter_by(username=username).one()
        user.is_active = is_active
        if status:
            user.status = status
        self.session.add(user)
        self.session.commit()

    def get_active_users(self):
        query = self.session.query(User).filter_by(is_active=True).all()
        return [entry.username for entry in query]

    def get_users_history(self):
        query = self.session.query(History).all()
        return [(entry.username, entry.ip_address, entry.login_timestamp) for entry in query]

    def set_all_users_inactive(self):
        for user in self.get_active_users():
            self.change_user_status(user, is_active=False)

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
            return True
        except NoResultFound:
            return False

    def add_contact(self, username: str, contact_name: str):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            contact = self.session.query(User).filter_by(username=contact_name).one()
            user.contacts.append(contact)
            self.session.query(Contact).filter_by(user_id=user.id, contact_id=contact.id).update({"is_active": True})
            self.session.commit()
            return True
        except NoResultFound:
            return False
