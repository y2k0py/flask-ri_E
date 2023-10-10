from spotipy.oauth2 import SpotifyOAuth
import random
import json
import config
from flask import Flask, request, url_for, session, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SESSION_COOKIE_NAME"] = 'Spotify Cookie'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:56RniQjprgfAtZFZw1pG@containers-us-west-190.railway.app:7312/railway"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_token = db.Column(db.String(750), unique=True, nullable=False)
    telegram_code = db.Column(db.String(20), unique=True, nullable=False)
    telegram_user_id = db.Column(db.BigInteger, unique=True)

    def __repr__(self):
        return f'users {self.id}'


with app.app_context():
    db.create_all()

app.secret_key = 'dfwefkewopfwoekfwf32'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    try:
        auth_url = create_oauth().get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        return render_template('error.html', error = 'index error')

@app.route('/redirect')
def redirect_page():
    session.clear()
    # code = request.args.get('code')
    try:
        code = request.args.get('code')
        token_info = create_oauth().get_access_token(code)
        session[TOKEN_INFO] = token_info
        return redirect(url_for('tgbotlink', _external=True))
    except Exception as e:
        return render_template('error.html', error = f'redirect error: {e}')

@app.route('/tgbotlink')
def tgbotlink():
    try:
        token_info = get_token()
        token_info_json = json.dumps(token_info)
        if token_info_json == 'null':
            return render_template('error.html', error =' json = null')

        existing_user = Users.query.filter_by(spotify_token=token_info_json).first()

        if existing_user:
            return render_template('redirectbot.html', random_numbers=existing_user.telegram_code)
        else:
            random_numbers = ''.join(random.choice('0123456789') for _ in range(20))
            existing_code = Users.query.filter_by(telegram_code=random_numbers).first()

            if existing_code is None:
                try:
                    save_code_to_db = Users(telegram_code=random_numbers, spotify_token=token_info_json)
                    db.session.add(save_code_to_db)
                    db.session.flush()
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    return render_template('error.html', error=f'db: {e}')

            return render_template('redirectbot.html',random_numbers=random_numbers)
    except Exception as e:
        return render_template('error.html', error = f'tg bot link: {e}')

def get_token():
    return session.get(TOKEN_INFO, None)

def create_oauth():
    return SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read user-library-modify user-top-read'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
