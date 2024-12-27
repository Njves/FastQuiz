import multiprocessing
import threading
from wsgiref.simple_server import make_server
import pytest
from app import create_app, db
from app.models import Answer, Question, Quiz, User
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

@pytest.fixture(scope="module")
def test_app():
    """Создаёт тестовое приложение Flask."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False  # Для упрощения тестов
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="module")
def live_server(test_app):
    """Запускает тестовый сервер Flask в отдельном потоке."""
    server = make_server("localhost", 5000, test_app)
    # Установите daemon=True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()  # Останавливает сервер после завершения тестов
    thread.join()


@pytest.fixture(scope="module")
def client(test_app):
    """Возвращает тестовый клиент Flask."""
    return test_app.test_client()


@pytest.fixture
def create_user():
    """Фикстура для создания пользователя."""
    def _create_user(username, password, is_guest=False):
        user = User(username=username, is_guest=is_guest)
        user.set_password(password)
        user.generate_token()
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user


@pytest.fixture
def simple_quiz(test_app):
    """Создает простой квиз с вопросами и ответами."""
    with test_app.app_context():
        quiz = Quiz(
            title="Test Quiz",
            description="A simple test quiz.",
            count_question=2
        )
        question1 = Question(
            text="What is the capital of France?",
            duration=30
        )
        question2 = Question(
            text="What is 2 + 2?",
            duration=20
        )
        answer1 = Answer(text="Paris", is_correct=True)
        answer2 = Answer(text="London", is_correct=False)
        answer3 = Answer(text="4", is_correct=True)
        answer4 = Answer(text="5", is_correct=False)

        question1.answers.extend([answer1, answer2])
        question2.answers.extend([answer3, answer4])

        quiz.questions.extend([question1, question2])
        db.session.add(quiz)
        db.session.commit()
        return {"quiz_id": quiz.id}


@pytest.fixture(scope="module")
def selenium_driver():
    """Создаёт веб-драйвер для Selenium."""
    options = Options()
    # options.add_argument("--headless")  # Headless режим
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def base_url(test_app):
    """Возвращает базовый URL приложения."""
    return "http://localhost:5000"


@pytest.fixture
def prepare_data(test_app, create_user, simple_quiz):
    """Создаёт тестового пользователя и квиз."""
    with test_app.app_context():
        user = create_user("testuser", "password123")
        quiz_data = simple_quiz
        return {"user": user, "quiz_id": quiz_data["quiz_id"]}
    
@pytest.fixture
def login_for_test(selenium_driver, live_server, base_url, prepare_data):
    selenium_driver.get(f"{base_url}/login")
    assert "login" in selenium_driver.current_url
    username_field = selenium_driver.find_element(By.NAME, "username")
    password_field = selenium_driver.find_element(By.NAME, "password")
    login_button = selenium_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    username_field.send_keys("testuser")  # Replace with valid username
    password_field.send_keys("password123")  # Replace with valid password
    login_button.click()