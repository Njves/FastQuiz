from flask import jsonify, render_template, request
from app.models import Quiz, Question, Answer, User

from app.main import bp


@bp.route('/', methods=['GET'])
def index():
    return render_template('base.html')


@bp.route('/start_quiz', methods=['POST'])
def start_quiz():
    # user_id = request.json.get('user_id')
    quiz_id = request.json.get('quiz_id')
    session_data = {'current_question_index': 0, 'score': 0}
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    first_question = quiz.questions.all()[0] if quiz.questions else None
    print(first_question)
    if not first_question:
        return jsonify({'message': 'No questions available for this quiz'}), 404
    answers = Answer.query.filter_by(question_id=first_question.id).all()
    answers_list = [{'id': answer.id, 'text': answer.text} for answer in answers]
    return jsonify({
        'message': 'Quiz started',
        'session_data': session_data,
        'question': {
            'id': first_question.id,
            'text': first_question.text,
            'answers': answers_list
        }
    })


@bp.route('/next_question', methods=['POST'])
def next_question():
    # user_id = request.json.get('user_id')
    session_data = request.json.get('session_data')
    quiz_id = request.json.get('quiz_id')
    quiz = Quiz.query.get(quiz_id)
    questions = list(quiz.questions)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    next_question_index = session_data['current_question_index'] + 1
    if next_question_index < len(questions):
        current_question = questions[next_question_index]
        answers = [{'id': answer.id, 'text': answer.text} for answer in current_question.answers]
        session_data['current_question_index'] += 1

        return jsonify({
            'session_data': session_data,
            'question': {
                'id': current_question.id,
                'text': current_question.text,
                'answers': answers
            }
        })
    else:
        return finish_quiz()



@bp.route('/submit_answer', methods=['POST'])
def submit_answer():
    # user_id = request.json.get('user_id')
    answer_id = request.json.get('answer_id')
    session_data = request.json.get('session_data')

    answer = Answer.query.get(answer_id)
    if not answer:
        return jsonify({'message': 'Answer not found'}), 404

    if answer.is_correct:
        session_data['score'] += 1
        result = 'correct'
    else:
        result = 'incorrect'

    return jsonify({'result': result, 'session_data': session_data})


@bp.route('/finish_quiz', methods=['POST'])
def finish_quiz():
    # добавить передачу юзера и сохранение результата в бд
    session_data = request.json.get('session_data')
    final_score = session_data['score']
    return jsonify({'score': final_score, 'message': 'Quiz finished'})
