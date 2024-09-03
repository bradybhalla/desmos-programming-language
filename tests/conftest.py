import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from tests.utils import CHROMEDRIVER_PATH, CHROME_OPTIONS


@pytest.fixture(scope="module")
def driver():
    """
    Fixture to get webdriver
    """
    driver = webdriver.Chrome(
        service=Service(executable_path=str(CHROMEDRIVER_PATH)), options=CHROME_OPTIONS
    )
    yield driver
    driver.close()

