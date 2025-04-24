from datetime import datetime
import secrets


from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import jwt

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
                       db.Column('text_answer', db.String(), nullable=True),
                       db.Column('is_correct', db.Boolean, default=False),
                       db.Column('submitted_at', db.DateTime,
                                 default=datetime.utcnow),
                       db.Column('attempt_id', db.Integer, db.ForeignKey(
                           'attempt.id', ondelete='CASCADE'))
                       )


quiz_score = db.Table('quiz_score',
                      db.Column('user_id', db.Integer, db.ForeignKey(
                          'user.id', ondelete='CASCADE')),
                      db.Column('quiz_id', db.Integer, db.ForeignKey(
                          'quiz.id', ondelete='CASCADE')),
                      db.Column('score', db.Integer)
                      )

quiz_creator = db.Table('quiz_creator',
                        db.Column('user_id', db.Integer, db.ForeignKey(
                            'user.id', ondelete='CASCADE')),
                        db.Column('quiz_id', db.Integer, db.ForeignKey(
                            'quiz.id', ondelete='CASCADE')))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.request_loader
def load_user_from_request(request):
    token = request.args.get('token')
    if token:
        user = User.query.filter_by(token=token).first()
        if user:
            return user

    token = request.headers.get('Authorization')
    if token:
        token = token.replace('Bearer ', '', 1)
        user = User.query.filter_by(token=token).first()
        if user:
            return user
    return None


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    password_hash = db.Column(db.String(256))
    quizzes_created = db.relationship(
        'Quiz', secondary=quiz_creator, backref='creators', lazy='dynamic')
    is_guest = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(256), unique=True, nullable=True)
    role = db.Column(db.String(5), nullable=False, default='user')

    def __repr__(self) -> str:
        return f'User {self.id}, Username: {self.username}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        token = secrets.token_hex(32)
        # Проверка уникальности
        while User.query.filter_by(token=token).first() is not None:
            token = secrets.token_hex(32)
        self.token = token


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(), nullable=False)
    count_question = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    password = db.Column(db.String())
    questions = db.relationship(
        'Question', secondary=quiz_question, backref='quizzes', lazy='dynamic')

    def __repr__(self):
        return f'Quiz {self.id}, Title: {self.title}, Description: {self.description}, Questions: {self.count_question}'

    def archive(self):
        """Архивирует квиз"""
        self.is_archived = True

    def restore(self):
        """Восстанавливает квиз из архива"""
        self.is_archived = False
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'count_question': self.count_question,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_archived': self.is_archived,
            'password': self.password,
            'questions': [q.to_dict() for q in self.questions]
        }


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    # Длительность в секундах (по умолчанию 30 секунд)
    duration = db.Column(db.Integer, nullable=False, default=30)
    question_type = db.Column(
        db.String(10), nullable=False, default='choice')  # 'choice' или 'text'
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'Question {self.id}, Text: {self.text}, question_type: {self.question_type}'

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'duration': self.duration,
            'question_type': self.question_type,
            'answers': [a.to_dict() for a in self.answers]
        }


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey(
        'question.id', ondelete='CASCADE'))

    def __repr__(self):
        return f'Answer {self.id}, Text: {self.text}, Is Correct: {self.is_correct}'
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'is_correct': self.is_correct
        }


class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'))
    quiz_id = db.Column(db.Integer, db.ForeignKey(
        'quiz.id', ondelete='CASCADE'))
    attempt_id = db.Column(db.Integer, db.ForeignKey(
        'attempt.id', ondelete='CASCADE'))
    score = db.Column(db.Integer, default=0)
    current_question_index = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    current_question_end_time = db.Column(db.DateTime)
    room_id = db.Column(db.Integer, db.ForeignKey(
        'quiz_room.id'), nullable=True)
    is_current_question_answered = db.Column(db.Boolean, default=False)

    attempt = db.relationship('Attempt', backref='sessions')
    user = db.relationship('User', backref='quiz_sessions')
    quiz = db.relationship('Quiz', backref='sessions')
    room = db.relationship('QuizRoom', backref='sessions')

    def __repr__(self):
        return f'QuizSession {self.id}, User: {self.user_id}, Quiz: {self.quiz_id}, Score: {self.score}'


class QuizRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    room_code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    quiz = db.relationship('Quiz', backref='rooms')
    host = db.relationship('User', backref='hosted_rooms')

    def __repr__(self):
        return f'QuizRoom {self.id}, Quiz: {self.quiz_id}, Code: {self.room_code}, Host: {self.host_id}'


class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'))
    quiz_id = db.Column(db.Integer, db.ForeignKey(
        'quiz.id', ondelete='CASCADE'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref='attempts')
    quiz = db.relationship('Quiz', backref='attempts')

    def __repr__(self):
        return f'Attempt {self.id}, User: {self.user_id}, Quiz: {self.quiz_id}, Score: {self.score}'
