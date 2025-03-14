from datetime import datetime, timedelta

from flask import jsonify, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required

from app.models import Quiz, Question, Answer, User, QuizSession, quiz_score, user_answer

from app import db
from app.main import bp


@bp.route('/', methods=['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type=int) 
    per_page = 3
    pagination = Quiz.query.filter_by(is_archived=False).paginate(
        page=page, per_page=per_page, error_out=False
    )
    if page > pagination.pages:
        return redirect(url_for('main.index', page=pagination.pages))    
    quiz_list = pagination.items
    next_url = url_for('main.index', page=pagination.next_num) \
        if pagination.has_next else None
    prev_url = url_for('main.index', page=pagination.prev_num) \
        if pagination.has_prev else None
    return render_template('quiz/list.html', 
                           quiz_list=quiz_list, 
                           pagination=pagination, 
                           current_user=current_user,
                           page=page, 
                           next_url=next_url, 
                           prev_url=prev_url)


@bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    return render_template('quiz/quiz.html', quiz=quiz)


@bp.route('/quiz_state/<int:session_id>', methods=['GET'])
@login_required
def get_quiz_state(session_id):
    quiz_session = QuizSession.query.get(session_id)
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404
    quiz = Quiz.query.get(quiz_session.quiz_id)
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404

    questions = quiz.questions.all()
    current_index = quiz_session.current_question_index
    if current_index >= len(questions):
        return jsonify({
            'message': 'Quiz completed',
            'score': quiz_session.score
        })
    current_question = questions[current_index]
    question_type = current_question.question_type
    answers = [{'id': answer.id, 'text': answer.text}
               for answer in current_question.answers] if question_type == 'choice' else []
    remaining_time = max(
        (quiz_session.current_question_end_time -
         datetime.utcnow()).total_seconds(), 0
    )
    if quiz_session.is_current_question_answered:
        correct_answer = Answer.query.filter_by(
            question_id=current_question.id, is_correct=True).first()
        return jsonify({
            'message': 'Answer already submitted',
            'session_id': quiz_session.id,
            'quiz_id': quiz.id,
            'count_question': len(questions),
            'number': current_index,
            'score': quiz_session.score,
            'correct_answer_id': correct_answer.id,
            'is_correct': quiz_session.is_current_question_answered,
            'question': {
                'text': current_question.text,
                'type': question_type,
                'answers': answers
            }
        })
    return jsonify({
        'session_id': quiz_session.id,
        'quiz_id': quiz.id,
        'count_question': len(questions),
        'number': current_index,
        'score': quiz_session.score,
        'remaining_time': remaining_time,
        'duration': current_question.duration,
        'question': {
            'text': current_question.text,
            'type': question_type,
            'answers': answers
        }
    })


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
    quiz_session = QuizSession(user_id=current_user.id, quiz_id=quiz_id,
                               current_question_end_time=datetime.utcnow() + timedelta(seconds=first_question.duration))
    db.session.add(quiz_session)
    db.session.commit()
    answers = Answer.query.filter_by(question_id=first_question.id).all()
    answers = answers if first_question.question_type == 'choice' else []
    answers_list = [{'id': answer.id, 'text': answer.text}
                    for answer in answers]
    return jsonify({
        'message': 'Quiz started',
        'session_id': quiz_session.id,
        'count_question': quiz.count_question,
        'number': quiz_session.current_question_index,
        'duration': first_question.duration,
        'question': {
            'text': first_question.text,
            'type': first_question.question_type,
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
        quiz_session.is_current_question_answered = False
        current_question = questions[next_question_index]
        answers = [{'id': answer.id, 'text': answer.text}
                   for answer in current_question.answers]
        answers = answers if current_question.question_type == 'choice' else []
        quiz_session.current_question_index = next_question_index
        quiz_session.current_question_end_time = datetime.utcnow(
        ) + timedelta(seconds=current_question.duration)
        db.session.commit()

        return jsonify({
            'message': 'Next question retrieved',
            'session_id': quiz_session.id,
            'count_question': quiz.count_question,
            'number': quiz_session.current_question_index,
            'duration': current_question.duration,
            'question': {
                'text': current_question.text,
                'type': current_question.question_type,
                'answers': answers
            }
        })
    return jsonify({'message': 'No more questions available'}), 200


@bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    session_id = request.json.get('session_id')
    quiz_session = QuizSession.query.get(session_id)
    correct_answer_id = None
    correct_answer = None
    if not quiz_session:
        return jsonify({'message': 'Quiz session not found'}), 404
    question = Quiz.query.get(quiz_session.quiz_id).questions.all()[quiz_session.current_question_index]
    if not question:
        return jsonify({'message': 'Question not found'}), 404

    is_in_time = request.json.get('is_in_time', True)

    if datetime.utcnow() > quiz_session.current_question_end_time + timedelta(seconds=1):
        is_in_time = False

    if quiz_session.is_current_question_answered:
        return jsonify({'message': 'Answer already submitted'}), 400

    quiz_session.is_current_question_answered = True
    if question.question_type == "text":
        text_answer = request.json.get('text_answer', '').strip()
        if not text_answer:
            return jsonify({'message': 'Answer cannot be empty'}), 400
        correct_answer = question.answers[0]
        is_correct = True if correct_answer.lower() == text_answer.lower() else False
        
    else:
        answer_id = request.json.get('answer_id')
        answer = Answer.query.get(answer_id)
        correct_answer_id = Answer.query.filter_by(question_id=answer.question_id, is_correct=True).first().id
        if not answer:
            return jsonify({'message': 'Answer not found'}), 404
        is_correct = answer.is_correct if is_in_time else False
        if answer.is_correct and is_in_time:
            quiz_session.score += 1
    # Запись в бд перепроверить позже
    if not current_user.is_guest:
        user_ans = user_answer.insert().values(
            user_id=current_user.id,
            question_id=question.id,
            answer_id=answer_id if question.question_type == "choice" else None,
            text_answer=text_answer if question.question_type == "text" else None,
            is_correct=is_correct,
            submitted_at=datetime.utcnow()
        )
        db.session.execute(user_ans)

    db.session.commit()

    return jsonify({
        'message': 'Answer received',
        'correct_answer_id': correct_answer_id,
        'correct_answer': correct_answer_id,
        'session_id': quiz_session.id,
        'is_in_time': is_in_time
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
    db.session.commit()
    return jsonify({'score': final_score, 'message': 'Quiz finished'})


@bp.route('/create_quiz', methods=['POST'])
@login_required
def create_quiz():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    questions_data = data.get('questions')
    if not title or not description or not questions_data:
        return jsonify({"error": "Missing required fields"}), 400
    quiz = Quiz(
        title=title,
        description=description,
        count_question=len(questions_data)
    )
    db.session.add(quiz)
    for question_data in questions_data:
        question_text = question_data.get('text')
        question_time = question_data.get('duration')
        question_type = question_data.get('type')
        answers_data = question_data.get('answers')

        if not question_text or not answers_data or not question_time:
            return jsonify({"error": "Each question must have text and answers"}), 400

        question = Question(text=question_text, duration=question_time, question_type=question_type)
        quiz.questions.append(question)

        for answer_data in answers_data:
            answer_text = answer_data.get('text')
            is_correct = answer_data.get('is_correct', False)
            if not answer_text:
                return jsonify({"error": "Each answer must have text"}), 400
            answer = Answer(
                text=answer_text,
                is_correct=is_correct
            )
            question.answers.append(answer)
    quiz.creators.append(current_user)
    db.session.commit()

    return jsonify({"message": "Quiz created successfully", "quiz_id": quiz.id}), 201


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz_form():
    return render_template('quiz/create.html')


@bp.route('/profile')
@login_required
def profile():
    user = current_user
    # Получение созданных квизов
    quizzes_created = user.quizzes_created.all()

    # Получение результатов квизов с ID и количеством вопросов
    results = db.session.execute(
        db.select(
            Quiz.title,         # Название квиза
            quiz_score.c.score,  # Набранный результат
            Quiz.id,            # ID квиза
            Quiz.count_question  # Количество вопросов
        )
        .join(quiz_score, quiz_score.c.quiz_id == Quiz.id)
        .filter(quiz_score.c.user_id == user.id)
    ).all()

    # Рендеринг шаблона с новыми данными
    return render_template(
        'profile/profile.html',
        user=user,
        quizzes_created=quizzes_created,
        results=results
    )

@bp.route('/delete_quiz/<int:quiz_id>', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    print(quiz.creators)
    if current_user in quiz.creators:
        if quiz:
            db.session.delete(quiz)
            db.session.commit()
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Quiz not found"}), 404
    else:
            return jsonify({"error": "You not creator"}), 404
    
@bp.route('/archive_quiz/<int:quiz_id>', methods=['PATCH'])
@login_required
def archive_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        quiz.is_archived = True
        db.session.commit()
        return jsonify({"message": "Квиз архивирован"}), 200
    return jsonify({"message": "Квиз не найден"}), 404

@bp.route('/unarchive_quiz/<int:quiz_id>', methods=['PATCH'])
@login_required
def unarchive_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        quiz.is_archived = False
        db.session.commit()
        return jsonify({"message": "Квиз разархивирован"}), 200
    return jsonify({"message": "Квиз не найден"}), 404