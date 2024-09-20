from datetime import datetime


from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

quiz_question = db.Table('quiz_question',
                         db.Column('quiz_id', db.Integer, db.ForeignKey(
                             'quiz.id', ondelete='CASCADE')),
                         db.Column('question_id', db.Integer, db.ForeignKey(
                             'question.id', ondelete='CASCADE')))

user_answer = db.Table('user_answer',
                       db.Column('user_id', db.Integer, db.ForeignKey(
                           'user.id', ondelete='CASCADE')),
                       db.Column('question_id', db.Integer, db.ForeignKey(
                           'question.id', ondelete='CASCADE')),
                       db.Column('answer_id', db.Integer, db.ForeignKey(
                           'answer.id', ondelete='CASCADE')),
                       db.Column('is_correct', db.Boolean, default=False),
                       db.Column('submitted_at', db.DateTime,
                                 default=datetime.utcnow))


quiz_score = db.Table('quiz_score',
                      db.Column('user_id', db.Integer, db.ForeignKey(
                          'user.id', ondelete='CASCADE')),
                      db.Column('quiz_id', db.Integer, db.ForeignKey(
                          'quiz.id', ondelete='CASCADE')),
                      db.Column('score', db.Integer))

quiz_creator = db.Table('quiz_creator',
                        db.Column('user_id', db.Integer, db.ForeignKey(
                            'user.id', ondelete='CASCADE')),
                        db.Column('quiz_id', db.Integer, db.ForeignKey(
                            'quiz.id', ondelete='CASCADE')))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    quizzes_created = db.relationship(
        'Quiz', secondary=quiz_creator, backref='creators', lazy='dynamic')

    def __repr__(self) -> str:
        return f'User {self.id}, Username: {self.username}, email: {self.email}, date: {self.date},' \
               f' last_seen: {self.last_seen}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(), nullable=False)
    count_question = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    questions = db.relationship(
        'Question', secondary=quiz_question, backref='quizzes', lazy='dynamic')

    def __repr__(self):
        return f'Quiz {self.id}, Title: {self.title}, Description: {self.description}, Questions: {self.count_question}'


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'Question {self.id}, Text: {self.text}'


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey(
        'question.id', ondelete='CASCADE'))

    def __repr__(self):
        return f'Answer {self.id}, Text: {self.text}, Is Correct: {self.is_correct}'
