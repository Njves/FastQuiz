from datetime import datetime

from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from app.models import Quiz, Question, Answer, User, QuizSession, quiz_score, user_answer

from app import db
from app.main import bp


@bp.route('/', methods=['GET'])
def index():
    return render_template('base.html')

@bp.route('/quiz')
def quiz():
    return render_template('quiz/quiz.html')

@bp.route('/start_quiz', methods=['POST'])
@login_required
def start_quiz():
    quiz_id = request.json.get('quiz_id')
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    first_question = quiz.questions.all()[0] if quiz.questions else None
    if not first_question:
        return jsonify({'message': 'No questions available for this quiz'}), 404
    quiz_session = QuizSession(user_id=current_user.id, quiz_id=quiz_id)
    db.session.add(quiz_session)
    db.session.commit()
    answers = Answer.query.filter_by(question_id=first_question.id).all()
    answers_list = [{'id': answer.id, 'text': answer.text}
                    for answer in answers]
    return jsonify({
        'message': 'Quiz started',
        'session_id': quiz_session.id,
        'count_question': quiz.count_question,
        'number': quiz_session.current_question_index,
        'question': {
            'text': first_question.text,
            'answers': answers_list
        }
    })


@bp.route('/next_question', methods=['POST'])
@login_required
def next_question():
    # Получаем ID сессии из запроса
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404

    quiz = Quiz.query.get(quiz_session.quiz_id)
    questions = quiz.questions.all()
    next_question_index = quiz_session.current_question_index + 1
    if next_question_index < len(questions):
        current_question = questions[next_question_index]
        answers = [{'id': answer.id, 'text': answer.text}
                   for answer in current_question.answers]
        quiz_session.current_question_index = next_question_index
        db.session.commit()

        return jsonify({
            'message': 'Next question retrieved',
            'session_id': quiz_session.id,
            'count_question': quiz.count_question,
            'number': quiz_session.current_question_index,
            'question': {
                'text': current_question.text,
                'answers': answers
            }
        })
    return jsonify({'message': 'No more questions available'}), 200


@bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    answer_id = request.json.get('answer_id')
    session_id = request.json.get('session_id')

    answer = Answer.query.get(answer_id)
    if not answer:
        return jsonify({'message': 'Answer not found'}), 404
    quiz_session = QuizSession.query.get(session_id)
    if answer.is_correct:
        quiz_session.score += 1
        result = 'correct'
    else:
        result = 'incorrect'
    if not current_user.is_guest:
        user_ans = user_answer.insert().values(
            user_id=current_user.id,
            question_id=answer.question_id,
            answer_id=answer.id,
            is_correct=answer.is_correct,
            submitted_at=datetime.utcnow()
        )
        db.session.execute(user_ans)
        db.session.commit()
    return jsonify({
        'message': 'Answer received',
        'result': result,
        'session_id': quiz_session.id
    })


@bp.route('/finish_quiz', methods=['POST'])
@login_required
def finish_quiz():
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404
    final_score = quiz_session.score
    if not current_user.is_guest:
        record = quiz_score.insert().values(user_id=current_user.id,
                                            quiz_id=quiz_session.quiz_id, score=final_score)
        db.session.execute(record)
    db.session.delete(quiz_session)
    db.session.commit()  # Сохраняем изменения в базе данных
    return jsonify({'score': final_score, 'message': 'Quiz finished'})
