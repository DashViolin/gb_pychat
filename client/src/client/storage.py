from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.exc import NoResultFound

from client.model import Contact, Message, init_db


class ClientStorage:
    """
    Класс-обертка над ORM для взаимодействия клиента с базой данных
    """

    def __init__(self, username) -> None:
        session, db_path = init_db(username)
        self.session = session
        self.db_path = db_path

    def get_contact_list(self):
        query = self.session.query(Contact).all()
        return [(entry.username) for entry in query]

    def check_contact(self, contact: str):
        if self.session.query(Contact).filter_by(username=contact).count():
            return True
        else:
            return False

    def clear_contacts(self):
        self.session.query(Contact).delete()
        self.session.commit()

    def update_contacts(self, contacts: list):
        self.clear_contacts()
        for new_contact in contacts:
            self.add_contact(new_contact)

    def store_msg(self, contact: str, msg_text: str, timestamp: datetime, is_incoming: bool, is_delivered: bool = True):
        message = Message(
            contact=contact, text=msg_text, timestamp=timestamp, is_incoming=is_incoming, is_delivered=is_delivered
        )
        self.session.add(message)
        self.session.commit()

    def get_chat_messages(self, contact):
        try:
            messages = self.session.query(Message).filter_by(contact=contact).all()
        except NoResultFound:
            return []
        else:
            return [(entry.text, entry.is_incoming, entry.is_delivered, entry.timestamp) for entry in messages]

    def get_not_delivered_msgs(self, contact: str):
        try:
            messages = (
                self.session.query(Message)
                .filter(
                    and_(
                        Message.contact == contact,
                        Message.is_incoming == False,
                        Message.is_delivered == False,
                    )
                )
                .all()
            )
        except NoResultFound:
            return []
        else:
            return [(entry.id, entry.text) for entry in messages]

    def mark_msg_delivered(self, msg_id: int):
        try:
            msg = self.session.query(Message).filter_by(id=msg_id).one()
            msg.is_delivered = True
            self.session.commit()
        except NoResultFound:
            pass

    def add_contact(self, contact: str):
        try:
            self.session.query(Contact).filter_by(username=contact).one()
        except NoResultFound:
            contact_obj = Contact(username=contact)
            self.session.add(contact_obj)
            self.session.commit()

    def del_contact(self, contact: str):
        try:
            self.session.query(Contact).filter_by(username=contact).delete()
            self.session.commit()
        except NoResultFound:
            pass
