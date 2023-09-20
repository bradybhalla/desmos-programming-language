import pytest
from conftest import run_program_js

from desmos_compiler.desmos_implementation import DesmosExpr, DesmosImplementation


@pytest.mark.parametrize("program_input", [2, 3, 10])
def test_generate_js(driver, program_input):
    """
    Ensure `DesmosImplementation.generate_js` functions correctly on
    a simple manually-created program
    """
    js = DesmosImplementation.generate_js(
        [
            DesmosExpr(id="run", latex="R_{un} = a \\to a-1, O_{ut} \\to O_{ut} + a"),
            DesmosExpr(id="in", latex="I_{n} = 2"),
            DesmosExpr(id="out", latex="O_{ut} = 0"),
            DesmosExpr(id="done", latex="D_{one} = -a"),
            DesmosExpr(id="0", latex="a=I_{n}"),
        ]
    )
    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0

    # calculates 1 + 2 + ... + program_input
    assert output == program_input * (program_input + 1) // 2
