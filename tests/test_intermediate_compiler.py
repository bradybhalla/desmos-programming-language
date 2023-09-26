import pytest
from conftest import run_program_js
from desmos_compiler.ast import Assignment, ConditionalExpr, ConditionalGroup, DesmosLiteral, If, Program, Variable

from desmos_compiler.desmos_implementation import DesmosImplementation
from desmos_compiler.intermediate_compiler import IntermediateLineProgramCompiler


@pytest.fixture
def conditional_program():
    return Program(
        [
            Assignment(Variable("X"), DesmosLiteral("-1")),
            ConditionalGroup(
                [
                    If(
                        ConditionalExpr("I_{n}=1"),
                        [Assignment(Variable("X"), DesmosLiteral("0"))],
                    ),
                    If(
                        ConditionalExpr("I_{n}=2"),
                        [Assignment(Variable("X"), DesmosLiteral("0"))],
                    ),
                ],
                Assignment(Variable("X"), DesmosLiteral("I_{n}")),
            ),
            Assignment(Variable("O_{ut}"), DesmosLiteral("I_{n}+X")),
            Assignment(Variable("D_{one}"), DesmosLiteral("0")),
        ]
    )

# TODO: make this do something
@pytest.mark.parametrize("program_input", [10])
def test_conditional_program(driver, conditional_program, program_input):
    intermediate_prog = IntermediateLineProgramCompiler(conditional_program).compile()
    assert intermediate_prog.get_errors() == ""

    desmos_exprs = DesmosImplementation.generate_exprs(intermediate_prog)
    desmos_js = DesmosImplementation.generate_js(desmos_exprs)

    output, exit_code = run_program_js(
        driver=driver, desmos_js=desmos_js, program_input=program_input
    )
    assert exit_code == 0
