import pytest
from tests.utils import run_program_js
from desmos_compiler.assembler import assemble


@pytest.mark.parametrize(
    "output_type,out,done",
    [
        ("numeric", 0, 0),
        ("numeric", 1, 0),
        ("list", [1, 2, 3], 0),
        ("numeric", 5, 1),
        ("list", [4, 3, 2], 2),
    ],
)
def test_js_runner(driver, output_type, out, done):
    assembly = rf"""
    line OUT \to IN, NEXTLINE
    line GOTO label
    label label
    line DONE \to {done}
    """
    js = assemble(assembly)

    program_output = run_program_js(
        driver=driver, desmos_js=js, program_input=str(out), output_type=output_type
    )
    assert program_output.exit_code == done
    assert program_output.output == out


@pytest.fixture
def collatz_assembly_program():
    return r"""
    expr n=0
    expr l=0
    line n \to IN, l \to 0, NEXTLINE

    label main
    line \left\{n=1: (OUT \to l, DONE \to 0), \operatorname{mod}(n,2)=0: (l\to l+1, LINE \to LINE + 1), (l \to l+1, GOTO odd)\right\}

    line n \to \frac{n}{2}, GOTO main

    label odd
    line n \to 3\cdot n + 1, GOTO main
    """


@pytest.mark.parametrize("program_input", [1, 3, 7])
def test_assembler(driver, collatz_assembly_program, program_input):
    """
    Ensure `DesmosImplementation.generate_exprs` functions correctly
    on an assembly program
    """
    js = assemble(collatz_assembly_program)

    program_output = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert program_output.exit_code == 0

    # calculate the length of the Collatz sequence starting with program_input
    expected_output = 0
    n = program_input
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        expected_output += 1

    assert program_output.output == expected_output
