from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Song, Singer, User
engine = create_engine(
'sqlite:///catalog.db?check_same_thread=False'
)
engine = create_engine(
'postgresql://catalog:catalogdb@localhost/catalog'
)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

singer = Singer(user_id=1,name='Hozier')
session.add(singer)
session.commit()
session.query(Singer).all()
song = Song(user_id=1,name="Someone new",
            description="Made with love",
            album="ALBUM", year_released="2014",
            singer=singer)
session.add(song)
session.commit()
session.query(Song).all()
