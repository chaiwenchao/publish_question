# encoding: utf-8

import config
from flask  import Flask, render_template, url_for, request, redirect, session, g
from models import User
from models import Question, Answer
from exts import db
from sqlalchemy import or_
from functools import wraps

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

#登陆限制视图函数
def login_required(func):

    @wraps(func)
    def wrap(*args, **kwargs):
        if session.get('user_id'):
            ret = func(*args, **kwargs)
            return ret
        else:
            return redirect(url_for('login'))
    return wrap


@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index/')
def index():
    context = {
        'questions': Question.query.order_by("-create_time").all()
    }
    return render_template('index.html', **context)


@app.route('/detail/<id>/', methods=['GET'])
def detail(id):
    question = Question.query.filter(Question.id==id).first()

    return render_template('detail.html', question=question)



@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        phone = request.form.get('phone')
        password = request.form.get('password')

        user = User.query.filter(User.phone == phone, User.password == password).first()
        if user:
            session['user_id'] = user.id
            session.permanent = True

            return redirect(url_for('index'))
        return "登陆失败,请验证您的用户名、密码!!"

    return render_template('login.html')

@app.route('/reg/', methods = ['GET', 'POST'])
def reg():
    message = ''

    if request.method == 'POST':
        phone = request.form.get('phone')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not phone or not username :
            message =  'username or phone is null, please check out!'

            return render_template('reg.html', message=message)
        if password1 != password2:
            message += 'password is not yizhi.'
            return render_template('reg.html', message=message)

        user = User.query.filter(User.phone == phone).first()
        if user:
            message = 'username has been exsit!'
            return render_template('reg.html', message=message)

        user = User(phone=phone, username=username, password=password1)
        try:
            db.session.add(user)
            db.session.commit()

        except Exception as e:
            message = e
            db.session.rollback()
            return render_template('reg.html', message=e)
        print(url_for('login'))
        return redirect(url_for('login'))

    return render_template('reg.html')


@app.route('/question/', methods=['GET', 'POST'])
@login_required
def question():

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        question = Question(title=title, content=content)
        userid = session.get('user_id')
        if userid:
            user = User.query.filter(User.id==userid).first()
            question.author_id = user.id
            db.session.add(question)
            db.session.commit()

        return redirect(url_for('index'))
    return render_template('questions.html')

# @app.context_processor
# def my_content_processor():
#     user_id = session.get('user_id')
#     if user_id:
#         user = User.query.filter(User.id==user_id).first()
#         if user:
#             return "{'user':user}"
#         return {}

@app.route('/answer/', methods=['POST'])
@login_required
def answer():
    if request.method == 'POST':
        content = request.form.get('answer')
        question_id = request.form.get('question_id')

        answer = Answer(content=content)
        user_id = session.get('user_id')
        user = User.query.filter(User.id == user_id).first()
        question = Question.query.filter(Question.id == question_id).first()
        answer.author = user
        answer.question = question

        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('detail', id=question_id))


@app.route('/search/', methods=['POST', 'GET'])
def search():
    keyword = request.args.get('q')
    result = Question.query.filter(or_(Question.title.contains(keyword),
                                    Question.content.contains(keyword))).order_by(
                                    Question.create_time.desc()).all()
    if result:
        return render_template('index.html', questions=result)
    else:
        return render_template('warn.html')

@app.context_processor
def my_context_processor():
    user_id = session.get('user_id')
    user = User.query.filter(User.id == user_id).first()
    if user:
        return {'login_user': user.username}
    return {}

@app.route('/logout')
def logout():

    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=9000)
