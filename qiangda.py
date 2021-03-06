#coding:utf-8
from flask import Flask, render_template, session, redirect, url_for, escape, request
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.form import upload
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
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
babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
admin = Admin(app, name=u'后台管理系统')


class Setting(db.Model):
    __tablename__ = 'setting'
    id = db.Column(db.Integer, primary_key=True)
    nowid = db.Column(db.Integer, nullable=False)
    open = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Setting %d>' % self.nowid

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
    title = db.Column(db.Text, index=True, nullable=False)
    type = db.Column(db.Integer, nullable=False)
    requirePic = db.Column(db.Boolean, nullable=False)
    A = db.Column(db.Text)
    B = db.Column(db.Text)
    C = db.Column(db.Text)
    D = db.Column(db.Text)
    choiceanswer = db.Column(db.Integer)
    blankanswer = db.Column(db.Text)
    path = db.Column(db.Text)
    # pic = db.Column(db.LargeBinary)
    timer = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Problem %r>' % self.title

'''
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
    # path = db.Column(db.String)
    pic = db.Column(db.Binary)

    def __repr__(self):
        return '<Picture ProblemId %r Path %r>' % (self.id, self.path)
'''


class UserView(ModelView):
    form_choices = {
        'usertype': [
            ('1', u'管理员'),
            ('2', u'普通用户'),
        ],
    }
    column_labels = dict(
        username=u'用户名',
        password=u'密码',
        usertype=u'用户角色',
    )

class ProblemsView(ModelView):
    form_choices = {
        'type': [
            ('1', u'选择题'),
            ('2', u'填空题'),
        ],
        'choiceanswer':[
            ('1', 'A'),
            ('2', 'B'),
            ('3', 'C'),
            ('4', 'D'),
        ],
    }
    column_labels = dict(
        title=u'题面',
        type=u'题目类型',
        requriepic=u'是否有图片',
        choiceanswer=u'选择答案',
        blankanswer=u'填空答案',
        path=u'图片',
        timer=u'倒计时秒',
    )
    form_extra_fields = {
        'path': upload.ImageUploadField(label=u'图片', base_path=os.path.join(basedir, 'static/images')),
    }


class FileView(FileAdmin):
    can_delete_dirs = False
    can_mkdir = False
    allowed_extensions = ['jpg', 'png']


class AdminView(BaseView):
    @expose('/')
    def index(self):
        if 'usertype' not in session:
            return self.render('login.html')
        if 1 != session['usertype']:
            return self.render('login.html')
        problemid = request.args.get('problemid', None)
        open = request.args.get('open', '-1')
        pnum = Problems.query.count()
        if problemid is not None:
            problemid = int(problemid)
            if problemid <= 0:
                return self.render('admin.html', problemid=-1)
            elif problemid > pnum:
                return self.render('admin.html', problemid=-2)
            db.session.query(Setting).filter(Setting.id == 1).update({Setting.nowid: problemid})
            db.session.commit()
        pid = Setting.query.filter(Setting.id==1).first().nowid
        if open == '1':
            db.session.query(Setting).filter(Setting.id==1).update({Setting.open: True})
            db.session.commit()
        elif open == '0':
            db.session.query(Setting).filter(Setting.id == 1).update({Setting.open: False})
            db.session.commit()
        opened = Setting.query.filter(Setting.id==1).first().open
        if opened:
            p = Problems.query.filter(Problems.id == pid).first()
            data = {
                'pid': p.id,
                'title': p.title,
                'type': p.type,
                'requriepic': p.requirePic,
                'timer': p.timer,
                'A': p.A,
                'B': p.B,
                'C': p.C,
                'D': p.D,
                'choice': p.choiceanswer,
                'blank': p.blankanswer,
                'path': p.path
            }
            socketio.emit('new problem', data, namespace='/test', broadcast=True)
        # print pid, pnum
        return self.render('admin.html', problemid=pid, opened=opened, problemnum=pnum)


admin.add_view(AdminView(name=u'抢答控制'))
admin.add_view(UserView(User, db.session, name=u'用户'))
admin.add_view(ProblemsView(Problems, db.session, name=u'题目'))
admin.add_view(FileView(os.path.join(basedir, 'static/problempic'), '/static/', name=u'图片'))


'''
Routers
'''


@app.route('/')
def index():
    return render_template('index.html')


'''
@app.route('/control')
def admin():
    if 'usertype' in session:
        if session['usertype'] == 1:
            return render_template('admin.html')
    return redirect(url_for('login'))
'''

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
                    return redirect(url_for('admin.index'))
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
    return render_template('display.html', username=escape(session['username']))

'''
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
'''

@app.route('/display')
def display():
    return render_template('display.html')

'''
@app.route('/as')
def adf():
    socketio.emit('new problem',{'data': 'new problem'}, namespace='/test', broadcast=True)
    return 'Sent'
'''


@socketio.on('answer', namespace='/test')
def test_message(message):
    if 'username' in session['username']:
        print message['username'], 'answer'
        opened = Setting.query.filter(Setting.id==1).first().open
        if opened:
            p = Problems.query.filter(Problems.id==message['pid']).first()
            if p.type == 1:
                ans = chr(64+p.choiceanswer)
            else:
                ans = p.blankanswer
            emit('answered', {'username': message['username'], 'useranswer': message['answer'], 'rightanswer': ans}, namespace='/test', broadcast=True)
        else:
            emit('closed', {'msg': 'Closed'}, namespace='/test')

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
    emit('my response', {'data': 'Disconnected'})

if __name__ == '__main__':
    db.session.query(Setting).filter(Setting.id==1).update({Setting.nowid: 1, Setting.open: False})
    db.session.commit()
    socketio.run(app, debug=True)
    #app.run(debug=True)
