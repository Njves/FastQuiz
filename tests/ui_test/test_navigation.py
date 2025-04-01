from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_navigation_to_pages(selenium_driver, login_for_test, live_server):
   
    courses_link = WebDriverWait(selenium_driver, 3).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Список квизов"))
    )
    courses_link.click()
    assert "http://localhost:5000/" in selenium_driver.current_url
    courses = selenium_driver.find_elements(By.CLASS_NAME, "card-body")
    assert len(courses) == 1, "No courses displayed, check database or UI rendering"
    create_quiz_link = WebDriverWait(selenium_driver, 2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Создать квиз")))
    create_quiz_link.click()
    # Replace with actual page URL identifier
    assert "create" in selenium_driver.current_url

    profile_link = WebDriverWait(selenium_driver, 2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "testuser")))
    profile_link.click()
    assert "profile" in selenium_driver.current_url
    logout_link = WebDriverWait(selenium_driver, 2).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Выход"))
    )
    logout_link.click()
    # After logging out, should be redirected to login page
    assert "logout" in selenium_driver.current_url
    live_server.shutdown()