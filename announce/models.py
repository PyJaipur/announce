from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
import bottle_tools as bt

engine = create_engine(database_url)
Base = declarative_base()


class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    path = Column(String)


class Cred(Base):
    __tablename__ = "creds"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    var = Column(String)


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    description = Column(String)
    image_id = Column(Integer, ForeignKey("image.id"))
    actions_done = Column(JSON)

    def asdict(self):
        return dict(
            eventid=self.id,
            title=self.title,
            end=self.start.to_iso8601_string(),
            end=self.end.to_iso8601_string(),
            description=self.description,
            imageid=self.image_id,
            actions_done=self.actions_done,
        )


Base.metadata.create_all(engine)
Session = sessionmaker(engine)
bt.common_kwargs.update({"Event": Event, "Image": Image})
