import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_guest_quiz(client, selenium_driver, base_url, live_server,prepare_data):
    selenium_driver.get(f"{base_url}/login")
    assert "login" in selenium_driver.current_url
    login_button = selenium_driver.find_element(By.ID, "guest-login-btn")
    login_button.click()
    quiz_button = WebDriverWait(selenium_driver, 2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Запустить квиз")))
    quiz_button.click()
    WebDriverWait(selenium_driver, 10).until(
        EC.visibility_of_element_located((By.ID, "start-button"))
    )
    start_button = selenium_driver.find_element(By.ID, "start-button")
    start_button.click()
    time.sleep(2.5)
    WebDriverWait(selenium_driver, 10).until(
        EC.visibility_of_element_located((By.ID, "question-text"))
    )
    answer_buttons = selenium_driver.find_elements(
        By.CSS_SELECTOR, "#answer-buttons .btn")
    if answer_buttons:
        answer_buttons[0].click()

    WebDriverWait(selenium_driver, 10).until(
        EC.visibility_of_element_located((By.ID, "next-button"))
    )

    next_button = selenium_driver.find_element(By.ID, "next-button")
    next_button.click()
    time.sleep(3.5)
    WebDriverWait(selenium_driver, 10).until(
        EC.visibility_of_element_located((By.ID, "question-text"))
    )
    answer_buttons = selenium_driver.find_elements(
        By.CSS_SELECTOR, "#answer-buttons .btn")
    if answer_buttons:
        answer_buttons[0].click()
    next_button = selenium_driver.find_element(By.ID, "next-button")
    next_button.click()
    time.sleep(0.5)
    results_header = selenium_driver.find_element(By.CLASS_NAME, "quiz-header")
    result_paragraph = results_header.find_element(By.TAG_NAME, "p").text
    assert "Ваш результат: 1 из 2" == result_paragraph, "Квиз некорректно подсчитывает результат"
    live_server.shutdown()
