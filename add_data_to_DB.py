from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base , Song , Singer
engine  = create_engine('sqlite:///songsandsingers1.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


singer = Singer(name ='Hozier')
session.add(singer)
session.commit()
session.query(Singer).all()
song = Song(name = "Someone new", description = "Made with love", album = "ALBUM", year_released="2014", singer= singer)
session.add(song)
session.commit()
session.query(Song).all()

