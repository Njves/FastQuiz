from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired

class QuestionForm(FlaskForm):
    question_text = StringField('Question Text', validators=[DataRequired()])

class QuizForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    count_question = IntegerField('Количество вопросов', validators=[DataRequired()])
    questions = FieldList(FormField(QuestionForm), min_entries=1)
    submit = SubmitField('Создать')
