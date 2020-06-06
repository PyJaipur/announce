from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
import bottle_tools as bt
from secrets import token_urlsafe
from announce import const

engine = create_engine(const.database_url)
Base = declarative_base()


class AnonUser:
    id = tg_handle = None
    is_anon = True


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    tg_handle = Column(String, nullable=False)
    is_anon = False
    memberships = relationship("Member", backref="user")


class AuditLog(Base):
    __tablename__ = "auditlog"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    text = Column(String)
    group_id = Column(
        Integer, ForeignKey("group.id", ondelete="cascade"), nullable=False
    )


class Group(Base):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    credentials = relationship("Cred", backref="group", order_by="Cred.id")
    memberships = relationship("Member", backref="group", order_by="Member.id")
    auditlogs = relationship(
        "AuditLog", backref="group", order_by="desc(AuditLog.timestamp)"
    )

    @staticmethod
    def new_group(session, creator, **kwargs):
        g = Group(**kwargs)
        session.add(g)
        session.commit()
        session.add(Cred(name="all", value="-", group_id=g.id))
        session.add(Cred(name="manage", value="-", group_id=g.id))
        session.add(
            Member(
                user_id=creator.id,
                group_id=g.id,
                allowed_creds={"all": True, "manage": True},
            )
        )
        session.add(
            AuditLog(text=f"{creator.tg_handle} created the group", group_id=g.id)
        )
        session.commit()
        return g


class Member(Base):
    __tablename__ = "member"
    id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="cascade"), nullable=False)
    group_id = Column(
        Integer, ForeignKey("group.id", ondelete="cascade"), nullable=False
    )
    allowed_creds = Column(JSON, default={}, nullable=False)

    def has_credential(self, cred_name):
        if self.allowed_creds.get("all"):
            return True
        return self.allowed_creds.get(cred_name)


class Otp(Base):
    __tablename__ = "otp"
    id = Column(Integer, primary_key=True)
    tg_handle = Column(String, nullable=False)
    otp = Column(String, nullable=False)

    @staticmethod
    def loop_create(session, **kwargs):
        "Try to create a token and retry if uniqueness fails"
        while True:
            tok = Otp(otp=token_urlsafe(), **kwargs)
            session.add(tok)
            session.commit()
            return tok


class LoginToken(Base):
    __tablename__ = "logintoken"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="cascade"), nullable=False)
    token = Column(String, nullable=False, unique=True, primary_key=True)
    has_logged_out = Column(Boolean, default=False)
    user = relationship("User")

    @staticmethod
    def loop_create(session, **kwargs):
        "Try to create a token and retry if uniqueness fails"
        while True:
            tok = LoginToken(token=token_urlsafe(), **kwargs)
            session.add(tok)
            session.commit()
            return tok


class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    path = Column(String)


class Cred(Base):
    __tablename__ = "cred"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    group_id = Column(
        Integer, ForeignKey("group.id", ondelete="cascade"), nullable=False
    )


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    description = Column(String)
    image_id = Column(Integer, ForeignKey("image.id", ondelete="cascade"))
    actions_done = Column(JSON)

    def asdict(self):
        return dict(
            eventid=self.id,
            title=self.title,
            start=self.start.to_iso8601_string(),
            end=self.end.to_iso8601_string(),
            description=self.description,
            imageid=self.image_id,
            actions_done=self.actions_done,
        )


Base.metadata.create_all(engine)
Session = sessionmaker(engine)
bt.common_kwargs.update(
    {
        "Event": Event,
        "Image": Image,
        "Otp": Otp,
        "User": User,
        "Group": Group,
        "Member": Member,
        "LoginToken": LoginToken,
        "Cred": Cred,
        "AuditLog": AuditLog,
    }
)
