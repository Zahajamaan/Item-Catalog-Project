import sys
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Singer(Base):

    __tablename__ = 'singer'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    user = relationship(User)
    user_id = Column(Integer, ForeignKey('user.id'))


class Song(Base):

    __tablename__ = 'song'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    album = Column(String(250))
    description = Column (String(250))
    year_released = Column(String(8))
    singer_id = Column(Integer, ForeignKey('singer.id'))
    singer = relationship(Singer)
    user = relationship(User)
    user_id = Column(Integer, ForeignKey('user.id'))



    @property
    def serialize(self):
        return {
            'name':self.name,
            'description': self.description,
            'id': self.id,
            'year_released': self.year_released,
            'album': self.album,

        }



engine = create_engine(
    'sqlite:///songsandsingers1.db?check_same_thread=False'
)
Base.metadata.create_all(engine)