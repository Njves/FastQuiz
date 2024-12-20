def test_register_success(client):
    """Тест успешной регистрации."""
    response = client.post('/register', json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'
    assert 'token' in response.json


def test_register_existing_user(client, create_user):
    """Тест регистрации с уже существующим именем пользователя."""
    create_user(username="testuser1", password="password123")
    response = client.post('/register', json={
        "username": "testuser1",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json['error'] == 'Username already exists'


def test_register_without_username_password(client):
    """Тест регистрации без части данных"""
    response = client.post('/register', json={
        "username": "",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json['error'] == 'Username and password are required'
    response = client.post('/register', json={
        "username": "г",
        "password": ""
    })
    assert response.status_code == 400
    assert response.json['error'] == 'Username and password are required'


def test_login_success(client, create_user):
    """Тест успешного входа в систему."""
    create_user(username="testuser2", password="password123")
    response = client.post('/login', json={
        "username": "testuser2",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful'
    assert 'token' in response.json


def test_login_invalid_credentials(client, create_user):
    """Тест входа с неверными данными."""
    create_user(username="testuser3", password="password123")
    response = client.post('/login', json={
        "username": "testuser3",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json['error'] == 'Invalid credentials'


def test_guest_auth(client):
    """Тест гостевой авторизации."""
    response = client.post('/guest_auth', json={
        "username": None
    })
    assert response.status_code == 201
    assert 'token' in response.json
    assert 'username' in response.json
