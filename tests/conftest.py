from json import loads
from pathlib import Path
from time import sleep
from typing import Literal, NamedTuple

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from desmos_compiler.generate_desmos import DesmosExpr, generate_js

DESMOS_PATH = Path("../desmos/index.html").resolve()

CHROME_OPTIONS = webdriver.ChromeOptions()
# CHROME_OPTIONS.add_argument("--headless")

MAX_STEPS = 1000

PROG_SETUP_DELAY = 0.05
PROG_ACTION_DELAY = 0.05


@pytest.fixture(scope="module")
def driver():
    """
    Fixture to get webdriver
    """
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=CHROME_OPTIONS
    )
    yield driver
    driver.close()


class ProgramOutput(NamedTuple):
    output: str
    exit_code: int


def run_program(
    *,
    driver: webdriver.Chrome,
    desmos_js: str,
    program_input: str | None = None,
    output_type: Literal["numeric", "list"] = "numeric",
) -> ProgramOutput:
    """
    Run the Desmos program created by `desmos_js`.

    Parameters:
        - `driver`: the webdriver to use
        - `desmos_js`: javascript to generate desmos expressions
        - `program_input`: sets the "in" expression if provided
        - `output_type`: either "numeric" or "list" depending on the type of the "out" expression

    Returns `NamedTuple` with:
        - `output`: the final value of the "out" expression
        - `exit_code`: the final value of the "done" expression (>= 0)
    """
    driver.get("file://" + str(DESMOS_PATH))

    # create expressions
    driver.execute_script(desmos_js)
    sleep(PROG_SETUP_DELAY)

    # set input if provided
    if program_input is not None:
        driver.execute_script(
            generate_js([DesmosExpr(id="in", latex=f"I_{{n}} = {program_input}")])
        )
        sleep(PROG_ACTION_DELAY)

    # create variables to track output and if program is done
    get_expr_value = lambda name, var_type: loads(
        driver.execute_script(f"return JSON.stringify({name}.{var_type}Value)")
    )
    driver.execute_script(
        """
        selenium_track_output = calculator.HelperExpression({ latex: 'O_{ut}' }); 
        selenium_track_done = calculator.HelperExpression({ latex: 'D_{one}' });
        """
    )
    sleep(PROG_ACTION_DELAY)

    # find the button to execute the run action
    run_btn = driver.find_element(
        by=By.CSS_SELECTOR, value="div[expr-id='run'] div[aria-label='Run Action']"
    )

    # keep executing the run action until the program is done
    steps = 0
    while get_expr_value("selenium_track_done", "numeric") < 0:
        run_btn.click()
        sleep(PROG_ACTION_DELAY)
        steps += 1
        if steps > MAX_STEPS:
            raise AssertionError("Program ran for too many steps")

    # find and return the output
    return ProgramOutput(
        output=get_expr_value("selenium_track_output", output_type),
        exit_code=get_expr_value("selenium_track_done", "numeric"),
    )
