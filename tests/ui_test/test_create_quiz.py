import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.models import Quiz


def test_create_quiz_form(client, selenium_driver, base_url, login_for_test, live_server):
    create_quiz_link = WebDriverWait(selenium_driver, 2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Создать квиз")))
    create_quiz_link.click()
    assert "Создание новой викторины" in selenium_driver.page_source
    title_field = selenium_driver.find_element(By.ID, "title")
    description_field = selenium_driver.find_element(By.ID, "description")
    title_field.send_keys("Test Quiz Title")
    description_field.send_keys("Test Quiz Description")
    add_question_button = selenium_driver.find_element(By.ID, "add-question")
    add_question_button.click()
    question_text_field = selenium_driver.find_element(
        By.ID, "question-1-text")
    question_text_field.send_keys("What is 2 + 2?")
    add_answer_button = selenium_driver.find_element(
        By.CSS_SELECTOR, "#question-1 .add-answer")
    add_answer_button.click()
    answer_1_text = selenium_driver.find_element(By.ID, "answer-1-0-text")
    answer_1_correct = selenium_driver.find_element(
        By.ID, "answer-1-0-correct")
    answer_2_text = selenium_driver.find_element(By.ID, "answer-1-1-text")
    answer_1_text.send_keys("4")
    answer_1_correct.click()
    answer_2_text.send_keys("1")
    submit_button = WebDriverWait(selenium_driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    selenium_driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
    time.sleep(0.5)  # Небольшая задержка, чтобы страница успела прокрутиться
    submit_button.click()
    with client.application.app_context():
        quiz = Quiz.query.filter_by().all()
        print(quiz)
        quiz = Quiz.query.filter_by(title="Test Quiz Title").first()
        assert quiz is not None, "Викторина не добавлена в базу данных"
        assert quiz.description == "Test Quiz Description", f"Ожидался description: 'Test Quiz Description', но получен: {quiz.description}"
        assert len(quiz.questions.all()) == 1, "У викторины отсутствуют вопросы"
        question = quiz.questions[0]
        assert question.text == "What is 2 + 2?", f"Ожидался вопрос: 'What is 2 + 2?', но получен: {question.text}"
        assert len(question.answers.all()) == 2, "Количество ответов не совпадает"
        assert question.answers[0].text == "4", f"Ожидался ответ: '4', но получен: {question.answers[0].text}"
        assert question.answers[0].is_correct, "Ответ '4' должен быть правильным"
        assert question.answers[1].text == "1", f"Ожидался ответ: '1', но получен: {question.answers[1].text}"
        assert not question.answers[1].is_correct, "Ответ '1' должен быть неправильным"
    live_server.shutdown()
