from flask import Flask, render_template, \
    request, redirect, url_for, flash, jsonify
#from database_setup import Base, Singer, Song, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

import sys
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

from sqlalchemy.orm.exc import NoResultFound

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
    description = Column(String(250))
    year_released = Column(String(8))
    singer_id = Column(Integer, ForeignKey('singer.id'))
    singer = relationship(Singer)
    user = relationship(User)
    user_id = Column(Integer, ForeignKey('user.id'))

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'year_released': self.year_released,
            'album': self.album,

        }


app = Flask(__name__)
#APP_PATH = '/var/www/catalog/catalog/'
#CLIENT_ID = json.loads(open(APP_PATH + 'client_secrets.json', 'r').read())['web']['client_id']
CLIENT_ID = json.loads(
    open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Singers And Songs Application"
engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
engine = create_engine('postgresql://catalog:catalogdb@localhost/catalog')
Base.metadata.create_all(engine)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showlogin():
    if 'username' in login_session:
        singers = session.query(Singer).all()
        return render_template('index.html', singers=singers)
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token
    )
    h = httplib2.Http()
    result = json.loads(h.request(
        url, 'GET')[1].decode('utf-8'))

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."
        ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."
        ), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps(
                'Current user is already connected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if user exists
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful"


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'
        ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.', 400
            ))
        response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/singers/<int:singer_id>/JSON')
def singersListJSON(singer_id):
    songs = session.query(Song).filter_by(singer_id=singer_id)
    return jsonify(Song=[i.serialize for i in songs])


@app.route('/')
@app.route('/singers/')
def singersInedx():
    singers = session.query(Singer).all()
    if singers is None:
        singers = []
    if 'username' not in login_session:
        return render_template('unauthenticated_index.html', singers=singers)
    return render_template('index.html', singers=singers)


@app.route('/singers/<int:singer_id>/')
def songsList(singer_id):
    singer = session.query(Singer).filter_by(id=singer_id).first()
    songs = session.query(Song).filter_by(singer_id=singer_id)
    creator = getUserInfo(singer.user_id)
    singers = session.query(Singer).all()
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('publicsonglist.html', singer=singer,
                               songs=songs, singers=singers,
                               creator=creator)
    else:
        return render_template('songlist.html',
                               singer=singer,
                               songs=songs,
                               singers=singers,
                               creator=creator)


@app.route('/singer/new', methods=['GET', 'POST'])
def newSinger():
    singers = session.query(Singer).all()
    if 'username' not in login_session:
        flash("you need to login first")
        return render_template('unauthenticated_index.html', singers=singers)
    if request.method == 'POST':
        newSong = Singer(name=request.form['name'],
                         user_id=login_session['user_id'])
        session.add(newSong)
        session.commit()
        flash("new Song added !")

        return redirect(url_for('singersInedx', singers=singers))
    else:
        return render_template('newsinger.html', singers=singers)


@app.route('/songs/<int:singer_id>/new', methods=['GET', 'POST'])
def newSong(singer_id):
    singers = session.query(Singer).all()
    if 'username' not in login_session:
        flash("you need to login first")
        return render_template('unauthenticated_index.html', singers=singers)
    if request.method == 'POST':
        newSong = Song(name=request.form['name'],
                       user_id=login_session['user_id'],
                       singer_id=singer_id,
                       description=request.form['description'],
                       album=request.form['album'],
                       year_released=request.form['year_released'])
        session.add(newSong)
        session.commit()
        flash("new Song added !")

        return redirect(url_for('songsList',
                                singer_id=singer_id,
                                singers=singers
                                ))
    else:
        return render_template('newsong.html',
                               singer_id=singer_id,
                               singers=singers)


@app.route('/singers/<int:singer_id>/<int:song_id>/JSON/')
def songsJSON(singer_id, song_id):
    song = session.query(Song).filter_by(id=song_id).one()
    return jsonify(Song=song.serialize)


@app.route('/songs/<int:singer_id>/<int:song_id>/edit',
           methods=['GET', 'POST'])
def editSong(singer_id, song_id):
    singers = session.query(Singer).all()
    if 'username' not in login_session:
        singers = session.query(Singer).all()
        flash("you need to login first")
        return render_template('unauthenticated_index.html', singers=singers)
    editedSong = session.query(Song).filter_by(id=song_id).one()
    if editedSong.user_id != login_session['user_id']:
        return """<script>function myFunction() {alert('You are not
         authorized to make changes to this song. Please
        create your own song in order to make changes.');}
        </script><body onload='myFunction()''>"""
    if request.method == 'POST':
        if request.form['name']:
            editedSong.name = request.form['name']
        session.add(editedSong)
        session.commit()
        flash("The song has been edited !")

        return redirect(url_for('songsList',
                                singer_id=singer_id, singers=singers
                                ))
    else:
        # USE THE RENDER_TEMPLATE FUNCTION BELOW TO SEE THE VARIABLES YOU
        # SHOULD USE IN YOUR EDITMENUITEM TEMPLATE
        return render_template('editsong.html', singer_id=singer_id,
                               song_id=song_id, song=editedSong,
                               singers=singers)


@app.route('/songs/<int:singer_id>/<int:song_id>/delete',
           methods=['GET', 'POST'])
def deleteSong(singer_id, song_id):
    singers = session.query(Singer).all()
    if 'username' not in login_session:
        flash("you need to login first")
        return render_template('unauthenticated_index.html', singers=singers)
    songToDelete = session.query(Song).filter_by(id=song_id).one()
    if songToDelete.user_id != login_session['user_id']:
        return """<script>function myFunction()
        {alert('You are not authorized to make changes to this song. Please
               create your own song in order to make changes.');}
               </script><body onload='myFunction()''>"""
    if request.method == 'POST':
        session.delete(songToDelete)
        session.commit()
        flash("The song has been deleted !")
        return redirect(url_for('songsList', singer_id=singer_id))
    else:
        return render_template('deletesong.html',
                               song=songToDelete, singers=singers)


if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True

    app.run(host='0.0.0.0', port=8000)
    app.run()
