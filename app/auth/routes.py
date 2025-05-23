import random

from flask import jsonify, redirect, render_template, url_for
from flask import request
from flask_login import login_user, logout_user, login_required

from app import db, login_manager
from app.auth import bp
from app.models import User
import jwt

@login_manager.request_loader
def load_user_from_request(request):
    token = request.headers.get('Authorization')
    if token:
        user = User.query.filter_by(token=token).first()
        if user:
            return user
    if token:
        token = token.replace('Bearer ', '', 1)
        return User.query.filter_by(token=token).first()
    return None


@bp.route('/guest_auth', methods=['POST'])
def guest_auth():
    username = request.json.get('username')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    user = User(is_guest=True)
    user.generate_token()
    user.username = username if username is not None else user.token
    db.session.add(user)
    db.session.commit()
    if username is None:
        username = f'guest_{user.id}'
        counter = 0
        while User.query.filter_by(username=username).first() is not None:
            counter += 1
            username = f'guest_{user.id}_{counter}'
        user.username = username
        db.session.commit()
    login_user(user, remember=True)
    return jsonify({
        'token': user.token,
        'username': user.username,
        'message': 'New guest user created'
    }), 201


@bp.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    user = User(
        username=username
    )
    user.set_password(password)
    user.generate_token()
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({'message': 'User registered successfully', 'token': user.token}), 201


@bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    login_user(user, remember=True)
    return jsonify({'message': 'Login successful', 'token': user.token}), 200

@bp.route('/login')
def login_page():
    return render_template('auth/login.html')

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template('auth/login.html')
