import pytest
from conftest import run_program

from desmos_compiler.generate_desmos import DesmosExpr, generate_js


@pytest.mark.parametrize("program_input", [2, 3, 10])
def test_generate_js(driver, program_input):
    """
    Ensure `generate_js` functions correctly on a very simple program
    """
    js = generate_js(
        [
            DesmosExpr(id="run", latex="R_{un} = a \\to a-1, O_{ut} \\to O_{ut} + a"),
            DesmosExpr(id="in", latex="I_{n} = 2"),
            DesmosExpr(id="out", latex="O_{ut} = 0"),
            DesmosExpr(id="done", latex="D_{one} = -a"),
            DesmosExpr(id="0", latex="a=I_{n}"),
        ]
    )

    output, exit_code = run_program(
        driver=driver, desmos_js=js, program_input=program_input
    )

    assert exit_code == 0

    # calculates 1 + 2 + ... + program_input
    assert output == program_input * (program_input + 1) // 2
