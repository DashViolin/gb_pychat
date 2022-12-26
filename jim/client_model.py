from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker

from config import ClientConf

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)
    status = Column(Text, nullable=True, default=None)
    is_active = Column(Boolean, default=False, index=True)
    is_contact = Column(Boolean, default=True, index=True)


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(User.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    reciever_id = Column(
        Integer, ForeignKey(User.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(Text)
    timestamp = Column(DateTime)

    user = relationship("User", backref=backref("user", uselist=False), foreign_keys=[sender_id])
    contact = relationship("User", backref=backref("contact", uselist=False), foreign_keys=[reciever_id])


def init_db(username: str):
    db_path = ClientConf.DATA_DIR / f"jim_client_db_{username}.sqlite"
    conn_string = f"sqlite:///{db_path}?check_same_thread=false&uri=true"

    engine = create_engine(conn_string, future=True, echo=False, pool_recycle=7200)
    if not db_path.exists():
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session, db_path
