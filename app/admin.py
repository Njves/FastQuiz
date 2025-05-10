from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app import admin_app, db
from app.models import User, Quiz, Question, Answer, QuizSession, QuizRoom, Attempt, QuizComment


class SecurityModelView(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'


admin_app.add_view(SecurityModelView(User, db.session, endpoint='user'))
admin_app.add_view(SecurityModelView(Quiz, db.session, endpoint='quiz'))
admin_app.add_view(SecurityModelView(Question, db.session, endpoint='question'))
admin_app.add_view(SecurityModelView(Answer, db.session, endpoint='answer'))
admin_app.add_view(SecurityModelView(
    QuizSession, db.session, endpoint='quizsession'))
admin_app.add_view(SecurityModelView(QuizRoom, db.session, endpoint='quizroom'))
admin_app.add_view(SecurityModelView(Attempt, db.session, endpoint='attempt'))
admin_app.add_view(SecurityModelView(QuizComment, db.session, endpoint='quizcomment'))