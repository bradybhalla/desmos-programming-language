import pytest
from conftest import run_program_js
from desmos_compiler.assembler import assemble, DesmosExpr, generate_js


@pytest.fixture
def summation_expression_program():
    """
    Desmos expressions to calculate the sum 1 + 2 + ... + input
    """
    return [
        DesmosExpr(id="run", latex="R_{un} = a \\to a-1, O_{ut} \\to O_{ut} + a"),
        DesmosExpr(id="in", latex="I_{n} = 2"),
        DesmosExpr(id="out", latex="O_{ut} = 0"),
        DesmosExpr(id="done", latex="D_{one} = -a"),
        DesmosExpr(id="0", latex="a=I_{n}"),
    ]


@pytest.fixture
def collatz_assembly_program():
    return r"""
    reg n
    reg l

    line n \to IN, l \to 0, NEXTLINE

    label main
    line \left\{n=1: (OUT \to l, DONE \to 0), \operatorname{mod}(n,2)=0: (l\to l+1, NEXTLINE), (l \to l+1, GOTO odd)\right\}

    line n \to \frac{n}{2}, GOTO main

    label odd
    line n \to 3\cdot n + 1, GOTO main
    """


@pytest.mark.parametrize("program_input", [2, 3, 10])
def test_generate_js(driver, summation_expression_program, program_input):
    """
    Ensure `DesmosImplementation.generate_js` functions correctly on
    a simple program created with a list of Desmos expressions
    """
    js = generate_js(summation_expression_program)
    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0

    # calculates 1 + 2 + ... + program_input
    assert output == program_input * (program_input + 1) // 2


@pytest.mark.parametrize("program_input", [1, 3, 7])
def test_assemble(driver, collatz_assembly_program, program_input):
    """
    Ensure `DesmosImplementation.generate_exprs` functions correctly
    on an assembly program
    """
    js = assemble(collatz_assembly_program)

    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0

    # calculate the length of the Collatz sequence starting with program_input
    expected_output = 0
    n = program_input
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        expected_output += 1

    assert output == expected_output
