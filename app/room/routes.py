import random
import string
from flask import jsonify, request
from flask_login import login_required,current_user
from app import db
from app.room import bp
from app.models import Quiz, QuizRoom


@bp.route('/create_room', methods=['POST'])
@login_required
def create_room():
    quiz_id = request.json.get('quiz_id')
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404

    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    while QuizRoom.query.filter_by(room_code=room_code).first() is not None:
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    quiz_room = QuizRoom(quiz_id=quiz_id, room_code=room_code, host_id=current_user.id)
    db.session.add(quiz_room)
    db.session.commit()

    room_link = f"{request.host_url}join_room/{quiz_room.room_code}"
    return jsonify({'room_link': room_link, 'message': 'Room created successfully'})