from datetime import datetime
import random
import string
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.room import bp
from app.models import Answer, Quiz, QuizRoom, QuizSession, quiz_score, user_answer


@bp.route('/create_room', methods=['POST'])
@login_required
def create_room():
    quiz_id = request.json.get('quiz_id')
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404

    room_code = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=8))
    while QuizRoom.query.filter_by(room_code=room_code).first() is not None:
        room_code = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=8))

    quiz_room = QuizRoom(
        quiz_id=quiz_id, room_code=room_code, host_id=current_user.id)
    db.session.add(quiz_room)
    db.session.commit()
    return jsonify({'room_code': room_code, 'room_id': quiz_room.id, 'message': 'Room created successfully'})


@bp.route('/join_room', methods=['POST'])
@login_required
def join_room():
    room_code = request.json.get('room_code')
    quiz_room = QuizRoom.query.filter_by(room_code=room_code).first()
    if not quiz_room:
        return jsonify({'message': 'Room not found'}), 404
    existing_session = QuizSession.query.filter_by(
        user_id=current_user.id, room_id=quiz_room.id).first()
    if existing_session:
        return jsonify({
            'message': 'Already joined this room',
            'session_id': existing_session.id
        })
    quiz_session = QuizSession(
        user_id=current_user.id, quiz_id=quiz_room.quiz_id, room_id=quiz_room.id, current_question_index=-1)
    db.session.add(quiz_session)
    db.session.commit()
    return jsonify({
        'message': 'Joined room successfully',
        'session_id': quiz_session.id,
        'room_id': quiz_room.id
    })


@bp.route('/start_room_quiz', methods=['POST'])
@login_required
def start_room_quiz():
    quiz_id = request.json.get('quiz_id')
    room_id = request.json.get('room_id')
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404

    # Проверка: если указана комната, только хост может начать квиз
    room = QuizRoom.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    if room.host_id != current_user.id:
        return jsonify({'message': 'Only the room host can start the quiz'}), 403

    # Инициализация первой сессии и вопроса
    first_question = quiz.questions.all()[0] if quiz.questions else None
    if not first_question:
        return jsonify({'message': 'No questions available for this quiz'}), 404

    # Создаем сессию для хоста с привязкой к комнате
    quiz_session = QuizSession(
        user_id=current_user.id, quiz_id=quiz_id, room_id=room.id)
    db.session.add(quiz_session)
    db.session.commit()

    answers = [{'id': answer.id, 'text': answer.text}
               for answer in first_question.answers]
    return jsonify({
        'message': 'Quiz started in room',
        'session_id': quiz_session.id,
        'count_question': quiz.count_question,
        'number': quiz_session.current_question_index,
        'question': {
            'text': first_question.text,
            'answers': answers
        }
    })


@bp.route('/get_room_quiz_status', methods=['POST'])
@login_required
def get_room_quiz_status():
    room_id = request.json.get('room_id')
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    room = QuizRoom.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    # Получаем сессию хоста комнаты
    quiz_session_host = QuizSession.query.filter_by(
        user_id=room.host_id, room_id=room.id).first()
    if not quiz_session_host:
        return jsonify({'message': 'Quiz not start'}), 200
    quiz = quiz_session_host.quiz
    question_index_host = quiz_session_host.current_question_index
    questions = quiz.questions.all()

    if question_index_host >= len(questions):
        return jsonify({'message': 'Quiz is over'}), 200
    if question_index_host == quiz_session.current_question_index:
        return jsonify({'message': 'Wait next question'}), 200
    current_question = questions[question_index_host]
    answers = [{'id': answer.id, 'text': answer.text}
               for answer in current_question.answers]
    
    return jsonify({
            'message': 'Next question retrieved',
            'session_id': session_id,
            'count_question': quiz.count_question,
            'number': quiz_session_host.current_question_index,
            'question': {
                'text': current_question.text,
                'answers': answers
            }
        })


@bp.route('/next_question', methods=['POST'])
@login_required
def next_question():
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404
    room = QuizRoom.query.filter_by(room_id=quiz_session.room_id).first()
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    if room.host_id != current_user.id:
        return jsonify({'message': 'Only the room host can start the quiz'}), 403

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


@bp.route('/submit_answer_room', methods=['POST'])
@login_required
def submit_answer():
    answer_id = request.json.get('answer_id')
    session_id = request.json.get('session_id')
    answer = Answer.query.get(answer_id)
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404
    room = QuizRoom.query.filter_by(room_id=quiz_session.room_id).first()
    if not room:
        return jsonify({'message': 'Room not found'}), 404
    if not answer:
        return jsonify({'message': 'Answer not found'}), 404
    
    if answer.is_correct:
        quiz_session.score += 1
        result = 'correct'
    else:
        result = 'incorrect'

    session_host = QuizSession.query.filter_by(user_id=room.host_id, room_id=room.id).first()
    quiz_session.current_question_index = session_host.current_question_index
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


@bp.route('/finish_quiz_room', methods=['POST'])
@login_required
def finish_quiz():
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404

    # Получаем информацию о комнате, в которой проходит квиз
    room = QuizRoom.query.filter_by(id=quiz_session.room_id).first()
    if not room:
        return jsonify({'message': 'Room not found'}), 404
    users_scores = []
    for session in room.sessions:
        user = session.user
        user_score = QuizSession.query.filter_by(user_id=user.id, room_id=room.id).first()
        if user_score:
            users_scores.append({
                'username': user.username,
                'score': user_score.score
            })
    if not current_user.is_guest:
        record = quiz_score.insert().values(
            user_id=current_user.id,
            quiz_id=quiz_session.quiz_id,
            score=quiz_session.score
        )
        db.session.execute(record)
    db.session.delete(quiz_session)
    db.session.commit()
    return jsonify({
        'message': 'Quiz finished',
        'users_scores': users_scores
    })
