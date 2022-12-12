import json
from contextlib import suppress

from sqlalchemy.exc import IntegrityError, NoResultFound

from .server_model import Contact, History, Message, Session, User


class ServerStorage:
    def __init__(self) -> None:
        self.session = Session()
        self.set_all_users_inactive()

    def register_user(self, username, password=None, ip_address=None):
        try:
            user = self.session.query(User).filter_by(username=username).one()
        except NoResultFound:
            user = User(username=username, password=password)
        if ip_address:
            user.history.append(History(ip_address=ip_address))
        self.session.add(user)
        self.session.commit()

    def set_user_is_active(self, username: str, is_active=True):
        user = self.session.query(User).filter_by(username=username).one()
        user.is_active = is_active
        self.session.add(user)
        self.session.commit()

    def get_active_users(self):
        query = self.session.query(User).filter_by(is_active=True).all()
        yield from (entry.username for entry in query)

    def set_all_users_inactive(self):
        for user in self.get_active_users():
            self.set_user_is_active(user, is_active=False)

    def store_msg(self, user_from, user_to, msg: dict):
        user_from_query, user_to_query = self.register_contacts(user_from, user_to)
        contact_pair = (
            self.session.query(Contact).filter_by(user_id=user_from_query.id, contact_id=user_to_query.id).one()
        )
        msg_text = json.dumps(msg, ensure_ascii=False)
        contact_pair.messages.append(Message(text=msg_text))
        self.session.add(contact_pair)
        self.session.commit()

    def register_contacts(self, user_from, user_to):
        with suppress(IntegrityError):
            self.register_user(username=user_from)
            self.register_user(username=user_to)
        user_from_query = self.session.query(User).filter_by(username=user_from).one()
        user_to_query = self.session.query(User).filter_by(username=user_to).one()
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
                    messages = self.session.query(Message).filter_by(contact_id=pair.id, is_delivered=False)
                    yield from ((entry.id, json.loads(entry.text)) for entry in messages)
                except NoResultFound:
                    continue

    def mark_msg_is_delivered(self, msg_id: int):
        self.session.query(Message).filter_by(id=msg_id).update({"is_delivered": True})
        self.session.commit()