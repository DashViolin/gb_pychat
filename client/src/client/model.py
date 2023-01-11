import sqlite3

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import default_comparator

from client.config import ClientConf

Base = declarative_base()


class Contact(Base):
    """
    Таблица временного хранения контактов пользователя
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)


class Message(Base):
    """
    Таблица хранения сообщений в чатах пользователя
    """

    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    contact = Column(String, index=True)
    text = Column(Text)
    timestamp = Column(DateTime)
    is_incoming = Column(Boolean, default=False, index=True)
    is_delivered = Column(Boolean, default=False, index=True)


def init_db(username: str):
    """Функция инициализации сессии ORM и базы данных при её отсутствии"""
    db_path = ClientConf.DATA_DIR / f"jim_client_db_{username}.sqlite"
    conn_string = f"sqlite:///{db_path}?check_same_thread=false&uri=true"

    engine = create_engine(conn_string, future=True, echo=False, pool_recycle=7200)
    if not db_path.exists():
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session, db_path
