from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.exc import NoResultFound

from .client_model import Message, User, init_db


class ClientStorage:
    def __init__(self, username) -> None:
        session, db_path = init_db(username)
        self.session = session
        self.db_path = db_path

    def store_and_get_user(self, username: str, is_contact: bool):
        user = None
        try:
            user = self.session.query(User).filter_by(username=username).one()
        except NoResultFound:
            new_user = User(username=username, is_contact=is_contact)
            self.session.add(new_user)
            self.session.commit()
            user = self.session.query(User).filter_by(username=username).one()
        return user

    def get_user_status(self, username: str):
        user = self.store_and_get_user(username=username, is_contact=False)
        return user.status

    def set_user_status(self, username: str, status: str):
        user = self.store_and_get_user(username=username, is_contact=False)
        user.status = status
        self.session.add(user)
        self.session.commit()

    def get_contact_pair(self, user_from: str, user_to: str):
        sender = self.store_and_get_user(username=user_from, is_contact=True)
        reciever = self.store_and_get_user(username=user_to, is_contact=True)
        return sender, reciever

    def set_contact_activity(self, username: str, is_active=True):
        user = self.store_and_get_user(username=username, is_contact=True)
        user.is_active = is_active
        self.session.add(user)
        self.session.commit()

    def get_contact_list(self):
        query = self.session.query(User).all()
        users = [(entry.username, entry.is_active) for entry in query]
        return list(sorted(sorted(users, key=lambda x: x[0]), key=lambda x: x[1], reverse=True))

    def update_contacts(self, contacts: list):
        stored_contacts = {user for user, _ in self.get_contact_list()}
        server_contacts = set(contacts)
        new_contacts = server_contacts - stored_contacts
        for new_contact in new_contacts:
            self.store_and_get_user(new_contact, is_contact=True)

    def store_msg(self, user_from: str, user_to: str, msg_text: str, timestamp: datetime):
        sender, reciever = self.get_contact_pair(user_from=user_from, user_to=user_to)
        message = Message(sender_id=sender.id, reciever_id=reciever.id, text=msg_text, timestamp=timestamp)
        self.session.add(message)
        self.session.commit()

    def get_chat_messages(self, user, contact):
        sender, reciever = self.get_contact_pair(user_from=user, user_to=contact)
        try:
            messages = (
                self.session.query(Message)
                .filter(
                    or_(
                        and_(
                            (Message.sender_id == sender.id),
                            (Message.reciever_id == reciever.id),
                        ),
                        and_(
                            (Message.sender_id == reciever.id),
                            (Message.reciever_id == sender.id),
                        ),
                    )
                )
                .order_by(Message.timestamp)
                .all()
            )
        except NoResultFound:
            return []
        else:
            return [(entry.text, entry.user.username, entry.timestamp) for entry in messages]

    def add_contact(self, contact: str):
        self.store_and_get_user(username=contact, is_contact=True)
        self.set_contact_activity(username=contact, is_active=True)

    def del_contact(self, contact: str):
        self.store_and_get_user(username=contact, is_contact=True)
        self.set_contact_activity(username=contact, is_active=False)
