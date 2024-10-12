from pathlib import Path
import pytest
import os

from tests.utils import create_driver

@pytest.fixture(scope="module")
def driver(browser, project_root):
    """
    Fixture to get webdriver
    """
    driver = create_driver(browser, project_root, headless=True)
    yield driver
    driver.close()

@pytest.fixture(scope="module")
def project_root():
    return Path(__file__).parent.parent.resolve()

@pytest.fixture(scope="module")
def local_desmos_url(project_root):
    return f"file://{project_root}/desmos/index.html"

@pytest.fixture(scope="module")
def browser():
    if "BROWSER" in os.environ:
        return os.environ["BROWSER"]
    
    return "chrome"
