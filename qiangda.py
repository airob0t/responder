from flask import Flask, render_template, session, redirect, url_for, escape, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import os

'''
Configs
'''

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)
db = SQLAlchemy(app)

'''
Models
'''


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password = db.Column(db.String)
    usertype = db.Column(db.Integer)

    def __repr__(self):
        return '<User %r>' % self.username


class Problems(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, index=True)
    type = db.Column(db.Integer)
    requirePic = db.Column(db.Boolean)
    timer = db.Column(db.Integer)

    def __repr__(self):
        return '<Problem %r>' % self.title


class Options(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    A = db.Column(db.Text)
    B = db.Column(db.Text)
    C = db.Column(db.Text)
    D = db.Column(db.Text)
    answer = db.Column(db.Integer)

    def __repr__(self):
        return '<Options ProblemId %r Answer %r>' % (self.id, self.answer)


class FillBlankAnswer(db.Model):
    __tablename__ = 'fillblankanswer'
    id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    answer = db.Column(db.Text)

    def __repr__(self):
        return '<BlankAnswer ProblemId %r Answer %r>' % (self.id, self.answer)


class Picture(db.Model):
    __tablename__ = 'picture'
    id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    path = db.Column(db.String)

    def __repr__(self):
        return '<Picture ProblemId %r Path %r>' % (self.id, self.path)


'''
Routers
'''


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    if 'usertype' in session:
        if session['usertype'] == 1:
            return render_template('admin.html')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'POST' == request.method:
        # print request.form['username'], request.form['password']
        if 'username' in request.form and 'password' in request.form:
            user = User.query.filter_by(username=request.form['username']).first()
            username = user.username
            password = user.password
            usertype = user.usertype
            # print username,password
            if username == request.form['username'] and password == request.form['password']:
                session['username'] = username
                session['usertype'] = usertype
                # print usertype
                if usertype == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('answer'))
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('usertype', None)
    return redirect(url_for('login'))


@app.route('/answer')
def answer():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('answer.html')


@app.route('/problems')
def problems():
    if 'usertype' in session:
        if session['usertype'] == '1':
            return render_template('problems.html')
    return redirect(url_for('login'))


@app.route('/users')
def users():
    if 'usertype' in session:
        if session['usertype'] == '1':
            return render_template('users.html')
    return redirect(url_for('login'))


if __name__ == '__main__':
    # socketio.run(app)
    app.run(debug=True)
