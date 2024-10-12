from dataclasses import dataclass
from json import loads
from pathlib import Path

from selenium import webdriver

from typing import Literal
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService

from desmos_compiler.assembler import DesmosExpr, generate_js

BROWSER = "chrome"

MAX_STEPS = 1000

PROG_SETUP_DELAY = 0.05
PROG_ACTION_DELAY = 0.05

def create_driver(browser, project_root, headless=False):
    """
    Returns webdriver

    Supported: chrome, firefox
    """
    if browser == "chrome":
        path = project_root / "chromedriver"
        assert path.is_file(), "chromedriver not in expected location"
        service = ChromeService(str(path))
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        return webdriver.Chrome(service=service, options=options)

    elif browser == "firefox":
        path = project_root / "geckodriver"
        assert path.is_file(), "geckodriver not in expected location"
        service = FirefoxService(str(path))
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        return webdriver.Firefox(service=service, options=options)

    else:
        raise ValueError("Browser not supported")


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
    driver,
    desmos_js: str,
    desmos_url: str,
    program_input: str | None = None,
    output_type: Literal["numeric", "list"] = "numeric",
) -> ProgramOutput:
    """
    Run the Desmos program created by `desmos_js`.

    Arguments:
    `driver` -- the webdriver to use
    `desmos_js` -- javascript to generate desmos expressions
    `desmos_url` -- url to desmos instance
    `program_input` -- sets the "in" expression if provided
    `output_type` -- either "numeric" or "list" depending on the type of the "out" expression

    Returns the program result as a `ProgramOutput` object.
    """
    driver.get(desmos_url)

    # create expressions
    driver.execute_script("window." + desmos_js)
    sleep(PROG_SETUP_DELAY)

    # set input if provided
    if program_input is not None:
        driver.execute_script(
            "window." + generate_js([DesmosExpr(id="in", latex=f"I_{{n}} = {program_input}")])
        )
        sleep(PROG_ACTION_DELAY)

    # create variables to track output and if program is done
    get_expr_value = lambda name, var_type: loads(
        driver.execute_script(f"return JSON.stringify({name}.{var_type}Value)")
    )
    driver.execute_script(
        """
        window.selenium_track_output = window.Calc.HelperExpression({ latex: 'O_{ut}' });
        window.selenium_track_done = window.Calc.HelperExpression({ latex: 'D_{one}' });
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
        output=get_expr_value("window.selenium_track_output", output_type),
        exit_code=get_expr_value("window.selenium_track_done", "numeric"),
    )
