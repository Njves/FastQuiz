from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired

class QuestionForm(FlaskForm):
    question_text = StringField('Question Text', validators=[DataRequired()])

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    count_question = IntegerField('Number of Questions', validators=[DataRequired()])
    questions = FieldList(FormField(QuestionForm), min_entries=1)
    submit = SubmitField('Create Quiz')
