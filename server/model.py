from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from server.config import ServerConf

db_path = ServerConf.DB_CONFIG["URL"]

engine = create_engine(db_path, future=True, echo=False, pool_recycle=7200)
Base = declarative_base()


class Contact(Base):
    """
    Таблица контактов, связывающая таблицу пользователей в отношении "многие ко многим"
    """

    __tablename__ = "contact"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    contact_id = Column(Integer, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    __table_args__ = (UniqueConstraint(user_id, contact_id),)

    user = relationship("User", backref=backref("user", uselist=False), foreign_keys=[user_id], viewonly=True)
    contact = relationship("User", backref=backref("contact", uselist=False), foreign_keys=[contact_id], viewonly=True)


class User(Base):
    """
    Таблица для хранения зарегистрированных на сервере пользователей
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)
    password = Column(String)
    status = Column(Text)
    is_active = Column(Boolean, default=False, index=True)
    contacts = relationship(
        "User",
        secondary="contact",
        primaryjoin=id == Contact.user_id,
        secondaryjoin=id == Contact.contact_id,
    )


class History(Base):
    """
    Таблица с историей входов пользователей на сервер
    """

    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    login_timestamp = Column(DateTime, default=func.now())


Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
