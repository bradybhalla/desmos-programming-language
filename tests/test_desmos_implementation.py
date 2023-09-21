import pytest
from conftest import run_program_js

from desmos_compiler.desmos_implementation import DesmosExpr, DesmosImplementation
from desmos_compiler.intermediate import (
    Condition,
    ConditionalCommand,
    GotoLineCommand,
    IntermediateLineProgram,
    SetRegisterCommand,
)


@pytest.fixture
def summation_exprs_program():
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
def collatz_intermediate_program():
    """
    IntermediateLineProgram to calculate the length of a Collatz sequence
    starting with the input
    """
    prog = IntermediateLineProgram()
    prog.add_register("I_{n}", "1")
    prog.add_register("O_{ut}", "1")
    prog.add_register("D_{one}", "-1")
    prog.add_register("n", "I_{n}")
    prog.add_register("l", "0")
    prog.add_line(
        [
            ConditionalCommand(
                [
                    Condition(
                        "n=1",
                        [
                            SetRegisterCommand("O_{ut}", "l"),
                            SetRegisterCommand("D_{one}", "0"),
                        ],
                    ),
                    Condition(
                        "\\operatorname{mod}\\left(n,2\\right)=0",
                        [SetRegisterCommand("l", "l+1"), GotoLineCommand(1)],
                    ),
                    Condition("", [SetRegisterCommand("l", "l+1"), GotoLineCommand(2)]),
                ]
            )
        ]
    )
    prog.add_line([SetRegisterCommand("n", "\\frac{n}{2}"), GotoLineCommand(0)])
    prog.add_line([SetRegisterCommand("n", "3\\cdot n + 1"), GotoLineCommand(0)])
    
    return prog


@pytest.mark.parametrize("program_input", [2, 3, 10])
def test_generate_js(driver, summation_exprs_program, program_input):
    """
    Ensure `DesmosImplementation.generate_js` functions correctly on
    a simple program created with a list of Desmos expressions
    """
    js = DesmosImplementation.generate_js(summation_exprs_program)
    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0

    # calculates 1 + 2 + ... + program_input
    assert output == program_input * (program_input + 1) // 2


@pytest.mark.parametrize("program_input", [1, 3, 5, 7])
def test_generate_exprs(driver, collatz_intermediate_program, program_input):
    """
    Ensure `DesmosImplementation.generate_exprs` functions correctly
    on an intermediate program
    """
    assert collatz_intermediate_program.get_errors() == ""

    exprs = DesmosImplementation.generate_exprs(collatz_intermediate_program)
    js = DesmosImplementation.generate_js(exprs)

    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0

    # calculate the length of the Collatz sequence starting with program_input
    expected_output = 0
    n = program_input
    while n != 1:
        n = n//2 if n%2 == 0 else 3*n + 1
        expected_output += 1

    assert output == expected_output
