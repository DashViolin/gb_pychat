from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from config import ServerConf

db_path = ServerConf.DB_CONFIG["URL"]

engine = create_engine(db_path, future=True, echo=False, pool_recycle=7200)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    contact_id = Column(Integer, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)

    __table_args__ = (UniqueConstraint(user_id, contact_id),)

    messages = relationship("Message", backref="contact")


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contact.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    text = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    is_delivered = Column(Boolean, default=False, index=True)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)
    password = Column(String)
    is_active = Column(Boolean, default=False, index=True)
    contacts = relationship(
        "User",
        secondary="contact",
        primaryjoin=id == Contact.user_id,
        secondaryjoin=id == Contact.contact_id,
    )


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="history")
    ip_address = Column(String, nullable=False)
    login_timestamp = Column(DateTime, default=func.now())


Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    Base.metadata.create_all(engine)


# class EntityAssociation(Base):
#     __tablename__ = 'entity_association'

#     entity_parent_id = Column(Integer, ForeignKey('entity.id'), primary_key=True)
#     entity_child_id = Column(Integer, ForeignKey('entity.id'), primary_key=True)

# class Entity(Base):
#     __tablename__ = 'entity'

#     id = Column(Integer, primary_key=True)
#     name = Column(String)

#     entity_childs = relationship('Entity',
#                                  secondary='entity_association',
#                                  primaryjoin=id==EntityAssociation.entity_parent_id,
#                                  secondaryjoin=id==EntityAssociation.entity_child_id,
#                                  backref='childs')

#     entity_parents = relationship('Entity',
#                                   secondary='entity_association',
#                                   primaryjoin=id==EntityAssociation.entity_child_id,
#                                   secondaryjoin=id==EntityAssociation.entity_parent_id,
#                                   backref='parents')
