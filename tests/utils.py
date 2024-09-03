from dataclasses import dataclass
from json import loads
from pathlib import Path

from selenium import webdriver

from typing import Literal
from time import sleep

from selenium.webdriver.common.by import By

from desmos_compiler.assembler import DesmosExpr, generate_js

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DESMOS_PATH = PROJECT_ROOT / "desmos/index.html"
CHROMEDRIVER_PATH = PROJECT_ROOT / "chromedriver"

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.add_argument("--headless")

MAX_STEPS = 1000

PROG_SETUP_DELAY = 0.05
PROG_ACTION_DELAY = 0.05

@dataclass
class ProgramOutput:
    """
    output -- output of the program
    exit_code -- exit code of the program (0 for success)
    """

    output: int | list[int]
    exit_code: int

def run_program_js(
    *,
    driver: webdriver.Chrome,
    desmos_js: str,
    program_input: str | None = None,
    output_type: Literal["numeric", "list"] = "numeric",
) -> ProgramOutput:
    """
    Run the Desmos program created by `desmos_js`.

    Arguments:
    `driver` -- the webdriver to use
    `desmos_js` -- javascript to generate desmos expressions
    `program_input` -- sets the "in" expression if provided
    `output_type` -- either "numeric" or "list" depending on the type of the "out" expression

    Returns the program result as a `ProgramOutput` object.
    """
    print(desmos_js)
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
        selenium_track_output = Calc.HelperExpression({ latex: 'O_{ut}' });
        selenium_track_done = Calc.HelperExpression({ latex: 'D_{one}' });
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
