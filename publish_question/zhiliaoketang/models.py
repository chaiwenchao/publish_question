from exts import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(11), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100),nullable=False)


class Question(db.Model):
    __tablesname__ ='question'

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    #datetime.now()获取的是服务器第一次运行的时间，而datetime.now每次创建一个模型时获取的当前时间
    create_time = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))

    author = db.relationship('User', backref=db.backref('questions'))


class Answer(db.Model):
    __tablesname__ = 'answer'

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    content = db.Column(db.TEXT, nullable=False)
    question_id = db.Column(db.INTEGER, db.ForeignKey('question.id'))
    author_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    create_time = db.Column(db.DateTime, default=datetime.now)

    question = db.relationship('Question', backref=db.backref('answers'))
    author = db.relationship("User", backref=db.backref('answers'))


