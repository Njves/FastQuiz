from datetime import datetime, timedelta
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy import and_

from flask import current_app, Response, jsonify, render_template, request, flash, redirect, session, stream_with_context, url_for
from flask_login import current_user, login_required

from app.models import Attempt, Quiz, Question, Answer, User, QuizSession, quiz_score, user_answer, QuizComment

from app import db
from app.main import bp


@bp.route('/', methods=['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    per_page = 3
    query = Quiz.query.filter_by(is_archived=False)
    if search_query:
        query = query.filter(Quiz.title.ilike(
            f"%{search_query}%") | Quiz.description.ilike(f"%{search_query}%"))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
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
                           search_query=search_query,
                           page=page,
                           next_url=next_url,
                           prev_url=prev_url)


@bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    if not quiz.is_available():
        quiz.is_archived = True
        db.session.commit()
    if quiz.is_archived:
        return render_template('quiz/quiz_archived.html', quiz=quiz)
    if quiz.password:
        if session.get(f'quiz_access_{quiz_id}_{quiz.password}'):
            return render_template('quiz/quiz.html', quiz=quiz)
        if request.method == 'POST':
            user_password = request.form.get('password')
            print(user_password)
            if quiz.password == user_password:
                session[f'quiz_access_{quiz_id}_{quiz.password}'] = True
                return redirect(url_for('main.quiz', quiz_id=quiz_id))
            else:
                return render_template('quiz/password_prompt.html', quiz_id=quiz_id, error="Неверный пароль")
        return render_template('quiz/password_prompt.html', quiz_id=quiz_id)

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
    attempt = Attempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
    )
    db.session.add(attempt)
    db.session.commit()
    quiz_session = QuizSession(user_id=current_user.id, quiz_id=quiz_id,
                               current_question_end_time=datetime.utcnow() + timedelta(seconds=first_question.duration), attempt_id=attempt.id)
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
    question = Quiz.query.get(quiz_session.quiz_id).questions.all()[
        quiz_session.current_question_index]
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
        if not text_answer and is_in_time:
            return jsonify({'message': 'Answer cannot be empty'}), 400
        correct_answer = question.answers[0].text
        is_correct = True if correct_answer.lower(
        ) == text_answer.lower() and is_in_time else False
    else:
        answer_id = request.json.get('answer_id')
        answer = Answer.query.get(answer_id)
        correct_answer_id = Answer.query.filter_by(
            question_id=question.id, is_correct=True).first().id
        is_correct = answer.is_correct if is_in_time else False
    if is_correct:
        quiz_session.score += 1
    # Запись в бд перепроверить позже
    if not current_user.is_guest:
        user_ans = user_answer.insert().values(
            user_id=current_user.id,
            question_id=question.id,
            answer_id=answer_id if question.question_type == "choice" and is_in_time else None,
            text_answer=text_answer if question.question_type == "text" else None,
            is_correct=is_correct,
            attempt_id=quiz_session.attempt_id,
            submitted_at=datetime.utcnow()
        )
        db.session.execute(user_ans)

    db.session.commit()

    return jsonify({
        'message': 'Answer received',
        'correct_answer_id': correct_answer_id,
        'is_correct': is_correct,
        'correct_answer': correct_answer,
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
        quiz_session.finished_at = datetime.utcnow()
        quiz_session.attempt.completed_at = datetime.utcnow()
    else:
        db.session.delete(quiz_session)
        db.session.delete(quiz_session.attempt)
    db.session.commit()
    return jsonify({'score': final_score, 'attempt_id': quiz_session.attempt_id, 'message': 'Quiz finished', "is_guest": current_user.is_guest})


@bp.route('/create_quiz', methods=['POST'])
@login_required
def create_quiz():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    questions_data = data.get('questions')
    password = data.get('password')
    if not title or not description or not questions_data:
        return jsonify({"error": "Missing required fields"}), 400
    quiz = Quiz(
        title=title,
        description=description,
        count_question=len(questions_data),
        password=password
    )
    db.session.add(quiz)
    for question_data in questions_data:
        question_text = question_data.get('text')
        question_time = question_data.get('duration')
        question_type = question_data.get('type')
        answers_data = question_data.get('answers')

        if not question_text or not answers_data or not question_time:
            return jsonify({"error": "Each question must have text and answers"}), 400

        question = Question(
            text=question_text, duration=question_time, question_type=question_type)
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
    quizzes_created = user.quizzes_created.all()
    for quiz in quizzes_created:
        if not quiz.is_available():
            quiz.is_archived = True
            db.session.commit()
    sessions = [session for session in user.quiz_sessions if session.finished_at]
    results_dict = {
        session.attempt_id: {
            'quiz_title': session.quiz.title,
            'score': session.score,
            'quiz_id': session.quiz.id,
            'count_question': session.quiz.count_question,
            'attempt_id': session.attempt_id
        }
        for session in sessions
    }

    return render_template(
        'profile/profile.html',
        user=user,
        quizzes_created=quizzes_created,
        results=results_dict
    )


@bp.route('/delete_quiz/<int:quiz_id>', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
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
        quiz.start_time = None
        quiz.end_time = None
        quiz.is_archived = False
        db.session.commit()
        return jsonify({"message": "Квиз разархивирован"}), 200
    return jsonify({"message": "Квиз не найден"}), 404


@bp.route('/attempt/<int:attempt_id>', methods=['GET'])
@login_required
def get_user_answers(attempt_id):
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found"}), 404

    quiz_session = attempt.sessions[0]
    if not quiz_session or quiz_session.user_id != current_user.id:
        return jsonify({"error": "Access denied"}), 403

    CorrectAnswer = aliased(Answer)

    answers = db.session.query(
        Question.text.label("question"),
        user_answer.c.text_answer.label("user_answer"),
        Answer.text.label("answer"),
        user_answer.c.is_correct,
        db.session.query(CorrectAnswer.text)
        .filter(CorrectAnswer.question_id == Question.id, CorrectAnswer.is_correct == True)
        .scalar_subquery()
        .label("correct_answer")
    ).join(Question, Question.id == user_answer.c.question_id) \
        .outerjoin(Answer, Answer.id == user_answer.c.answer_id) \
        .filter(user_answer.c.attempt_id == attempt_id) \
        .all()

    result = [{
        "question": a.question,
        "user_answer": a.user_answer if a.user_answer is not None else a.answer,
        "correct_answer": a.correct_answer,
        "is_correct": int(a.is_correct)  # Преобразование в 0 или 1
    } for a in answers]

    total_score = sum(a['is_correct'] for a in result)

    return render_template('profile/attempt_result.html', result=result, total_score=total_score)


@bp.route('/quiz/<int:quiz_id>/set_password', methods=['POST'])
@login_required
def set_quiz_password(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.creators[0].id != current_user.id:
        return jsonify({"success": False, "message": "Вы не можете изменить пароль этого квиза"}), 403

    data = request.get_json()
    new_password = data.get("password")
    quiz.password = new_password

    db.session.commit()
    return jsonify({"success": True, "message": "Пароль успешно обновлен"})



@bp.route('/quiz/<int:quiz_id>/export_results', methods=['GET'])
@login_required
def export_quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.creators[0].id != current_user.id:
        return jsonify({"success": False, "message": "Вы не можете экспортировать результаты этого квиза"}), 403

    # Загружаем все попытки, чтобы избежать проблем с сессией
    attempts = db.session.query(Attempt).options(
        joinedload(Attempt.user),
        joinedload(Attempt.quiz)
    ).filter(
        and_(
            Attempt.quiz_id == quiz_id,
            Attempt.completed_at.isnot(None)
        )
    ).all()
    # Получаем все уникальные вопросы, чтобы сделать их заголовками
    questions = db.session.query(Question).join(user_answer, Question.id == user_answer.c.question_id) \
        .filter(user_answer.c.attempt_id.in_([a.id for a in attempts])) \
        .distinct().all()

    CorrectAnswer = aliased(Answer)

    # Загружаем ответы пользователей
    all_answers = []
    for attempt in attempts:
        answers = db.session.query(
            Question.text.label("question"),
            user_answer.c.text_answer.label("user_answer"),
            Answer.text.label("answer"),
            user_answer.c.is_correct,
            db.session.query(CorrectAnswer.text)
            .filter(CorrectAnswer.question_id == Question.id, CorrectAnswer.is_correct == True)
            .scalar_subquery()
            .label("correct_answer")
        ).join(Question, Question.id == user_answer.c.question_id) \
        .outerjoin(Answer, Answer.id == user_answer.c.answer_id) \
        .filter(user_answer.c.attempt_id == attempt.id) \
        .all()

        # Создаём словарь для ответов в колонках
        answer_dict = {
            "Пользователь": attempt.user.username,
            "Оценка": attempt.score,
            "Всего вопросов": attempt.quiz.count_question,
        }

        for q in questions:
            answer_entry = next((a for a in answers if a.question == q.text), None)
            if answer_entry is None:
                continue
            answer_dict[f"Вопрос: {q.text}"] = answer_entry.user_answer if answer_entry.user_answer else answer_entry.answer
            answer_dict[f"Правильный ответ"] = answer_entry.correct_answer if answer_entry else ""

        all_answers.append(answer_dict)

    # Закрываем сессию перед генерацией CSV
    db.session.close()

    def generate():
        # Формируем заголовки
        fieldnames = ["Пользователь", "Оценка", "Всего вопросов"] + \
                     [f"Вопрос: {q.text}" for q in questions] + \
                     [f"Правильный ответ" for _ in questions]

        yield ",".join(fieldnames) + "\n"

        # Заполняем строки пользователей
        for row in all_answers:
            yield ",".join(str(row.get(field, "")) for field in fieldnames) + "\n"

    response = Response(stream_with_context(generate()), content_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=quiz_{quiz_id}_results.csv"
    return response

@bp.route('/quiz/<int:quiz_id>/edit/soft', methods=['GET'])
@login_required
def edit_quiz_soft(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz/edit_quiz_soft.html', quiz=quiz)

@bp.route('/quiz/<int:quiz_id>/edit/soft', methods=['POST'])
@login_required
def update_quiz_soft(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.title = request.form['title']
    quiz.description = request.form['description']
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    quiz.start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
    quiz.end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
    for question in quiz.questions:
        new_text = request.form.get(f"question_{question.id}")
        if new_text:
            question.text = new_text
    db.session.commit()
    flash("Квиз обновлён (мягкое редактирование)", "success")
    return redirect(url_for('main.edit_quiz_soft', quiz_id=quiz.id))

# Жёсткое редактирование (создание нового квиза)
@bp.route('/quiz/<int:quiz_id>/edit/hard', methods=['GET'])
def edit_quiz_hard(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = [q.to_dict() for q in quiz.questions]
    return render_template("quiz/edit_quiz_hard.html", quiz=quiz.to_dict(), questions=questions)


@bp.route('/quiz/<int:quiz_id>/edit/hard', methods=['POST'])
def update_quiz_hard(quiz_id):
    old_quiz = Quiz.query.get_or_404(quiz_id)
    old_quiz.is_archived = True
    db.session.commit()

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    questions_data = data.get('questions')
    password = data.get('password')
    if not title or not description or not questions_data:
        return jsonify({"error": "Missing required fields"}), 400
    quiz = Quiz(
        title=title,
        description=description,
        count_question=len(questions_data),
        password=password
    )
    db.session.add(quiz)
    for question_data in questions_data:
        question_text = question_data.get('text')
        question_time = question_data.get('duration')
        question_type = question_data.get('type')
        answers_data = question_data.get('answers')

        if not question_text or not answers_data or not question_time:
            return jsonify({"error": "Each question must have text and answers"}), 400

        question = Question(
            text=question_text, duration=question_time, question_type=question_type)
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
    return jsonify({"redirect_url": url_for('main.edit_quiz_soft', quiz_id=quiz.id)})

@bp.route('/quiz/<int:quiz_id>/comment', methods=['POST'])
@login_required
def add_comment(quiz_id):
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Комментарий не может быть пустым'}), 400

    quiz = Quiz.query.get_or_404(quiz_id)
    comment = QuizComment(
        quiz_id=quiz.id,
        author_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Комментарий успешно добавлен'})

@bp.route('/quiz/<int:quiz_id>/comments')
def quiz_comments(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    comments = QuizComment.query.filter_by(quiz_id=quiz_id).order_by(QuizComment.created_at.desc()).all()
    return render_template('quiz/quiz_comments.html', quiz=quiz, comments=comments)