from app.models import Quiz, Question, Answer, User, quiz_score
from app import db

def test_quiz_flow(client, simple_quiz, create_user):
    """Тестирование прохождения квиза через API."""
    create_user(username="testquiz", password="password123")

    # Загружаем квиз и связанные данные внутри активной сессии
    with client.application.app_context():
        quiz = Quiz.query.get(simple_quiz["quiz_id"])
        questions = quiz.questions.all()
        answers = [
            answer for question in questions for answer in question.answers]

    # Аутентификация пользователя
    login_response = client.post('/login', json={
        "username": "testquiz",
        "password": "password123"
    })
    assert login_response.status_code == 200

    token = login_response.json.get("token")
    headers = {"Authorization": f"Bearer {token}"}

    # Стартуем квиз
    start_response = client.post(
        '/start_quiz', json={"quiz_id": quiz.id}, headers=headers)
    assert start_response.status_code == 200
    assert start_response.json["message"] == "Quiz started"
    session_id = start_response.json["session_id"]

    # Первый вопрос
    first_question = questions[0]

    for answer in answers:
        if answer.is_correct and answer.question_id == first_question.id:
            correct_answer = answer
        elif answer.question_id == first_question.id:
            uncorrect_answer = answer
    # Отправляем правильный ответ
    submit_response = client.post('/submit_answer', json={
        "session_id": session_id,
        "answer_id": correct_answer.id,
        "is_in_time": True
    }, headers=headers)
    assert submit_response.status_code == 200
    assert submit_response.json["message"] == "Answer received"
    # Отправляем второй ответ на тот же вопрос
    submit_response = client.post('/submit_answer', json={
        "session_id": session_id,
        "answer_id": uncorrect_answer.id,
        "is_in_time": True
    }, headers=headers)
    assert submit_response.status_code == 200
    assert submit_response.json["message"] == "Answer already submitted"
    next_response = client.post(
        '/next_question', json={"session_id": session_id}, headers=headers)
    assert next_response.status_code == 200
    assert next_response.json["message"] == "Next question retrieved"

    # Завершаем квиз
    finish_response = client.post(
        '/finish_quiz', json={"session_id": session_id}, headers=headers)
    assert finish_response.status_code == 200
    assert finish_response.json["message"] == "Quiz finished"
    assert finish_response.json["score"] == 1  # Ожидаемый результат
    with client.application.app_context():
        user = User.query.filter_by(username="testquiz").first()  # Получаем пользователя
        results = db.session.execute(
        db.select(
            Quiz.title,
            quiz_score.c.score,
            Quiz.id,
            Quiz.count_question
        )
        .join(quiz_score, quiz_score.c.quiz_id == Quiz.id)
        .filter(quiz_score.c.user_id == user.id)
    ).all()
    assert results == [('Test Quiz', 1, 1, 2)]