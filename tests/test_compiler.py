import pytest
from conftest import run_program_js
from desmos_compiler.assembler import assemble

from desmos_compiler.ast import Assignment, Variable, Literal, Group, Expression
from desmos_compiler.compiler import Compiler


@pytest.fixture
def assignment_program():
    return Group(
        [
            Assignment(Variable("X"), Expression([Variable("IN")])),
            Assignment(Variable("Y"), Expression([Literal("\\left("), Variable("X"), Literal("\\cdot 2 \\right)^3")])),
            Assignment(Variable("X"), Expression([Literal("5")])),
            Assignment(Variable("OUT"), Expression([Variable("Y")])),
            Assignment(Variable("DONE"), Expression([Literal("0")])),
        ]
    )


@pytest.mark.parametrize("program_input", [1,2])
def test_compiler(driver, assignment_program, program_input):
    compiler = Compiler()
    compiler.compile_statement(assignment_program)
    asm = compiler.generate_assembly()

    js = assemble(asm)
    output, exit_code = run_program_js(
        driver=driver, desmos_js=js, program_input=program_input
    )
    assert exit_code == 0
    assert output == 8*program_input**3
