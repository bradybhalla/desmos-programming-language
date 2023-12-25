import pytest
from conftest import run_program_js
from desmos_compiler.assembler import assemble

from desmos_compiler.syntax_tree import (
    Assignment,
    Declaration,
    DesmosType,
    If,
    Variable,
    Literal,
    Group,
    Expression,
    While,
)
from desmos_compiler.compiler import Compiler


def assignment_ast_program():
    return Group(
        [
            Declaration(Variable("X"), DesmosType("num")),
            Assignment(Variable("X"), Expression([Variable("$IN")])),
            Declaration(Variable("Y"), DesmosType("num")),
            Assignment(
                Variable("Y"),
                Expression(
                    [Literal("\\left("), Variable("X"), Literal("\\cdot 2 \\right)^3")]
                ),
            ),
            Assignment(Variable("X"), Expression([Literal("5")])),
            Assignment(Variable("$OUT"), Expression([Variable("Y")])),
            Assignment(Variable("$DONE"), Expression([Literal("0")])),
        ]
    )


def expected_assignment_ast(x):
    return 8 * x**3


def conditional_ast_program():
    create_mod_test = lambda n: Expression(
        [
            Literal(r"\operatorname{mod}\left("),
            Variable("x"),
            Literal(rf",{n}\right)=0"),
        ]
    )
    assign_output = lambda n: Assignment(
        Variable("$OUT"), Expression([Literal(f"{n}")])
    )
    return Group(
        [
            Declaration(Variable("x"), DesmosType("num")),
            Assignment(Variable("x"), Expression([Variable("$IN")])),
            assign_output(-1),
            If(
                create_mod_test(15),
                assign_output(0),
                If(
                    create_mod_test(5),
                    assign_output(1),
                    If(create_mod_test(3), assign_output(2), None),
                ),
            ),
            Assignment(Variable("$DONE"), Expression([Literal("0")])),
        ]
    )


def expected_conditional_ast(x):
    res = -1
    if x % 15 == 0:
        res = 0
    elif x % 5 == 0:
        res = 1
    elif x % 3 == 0:
        res = 2
    return res


def while_ast_program():
    assign_var = lambda v1, v2: Assignment(Variable(v1), Expression([Variable(v2)]))
    assign_literal = lambda v, l: Assignment(Variable(v), Expression([Literal(l)]))
    return Group(
        [
            Declaration(Variable("counter"), DesmosType("num")),
            assign_var("counter", "$IN"),
            Declaration(Variable("x"), DesmosType("num")),
            Declaration(Variable("y"), DesmosType("num")),
            assign_literal("x", "1"),
            assign_literal("y", "0"),
            While(
                Expression([Variable("counter"), Literal("> 0")]),
                Group(
                    [
                        Declaration(Variable("tmp"), DesmosType("num")),
                        assign_var("tmp", "x"),
                        assign_var("x", "y"),
                        Assignment(
                            Variable("y"),
                            Expression([Variable("y"), Literal("+"), Variable("tmp")]),
                        ),
                        Assignment(
                            Variable("counter"),
                            Expression([Variable("counter"), Literal("-1")]),
                        ),
                    ]
                ),
            ),
            assign_var("$OUT", "y"),
            Assignment(Variable("$DONE"), Expression([Literal("0")])),
        ]
    )


# fibonacci sequence
def expected_while_ast(x):
    i = 1
    j = 0
    for _ in range(x):
        i, j = j, i + j
    return j


@pytest.mark.parametrize("program_inputs", [[0, 10, 15]])
@pytest.mark.parametrize(
    "program",
    [
        (assignment_ast_program, expected_assignment_ast),
        (conditional_ast_program, expected_conditional_ast),
        (while_ast_program, expected_while_ast),
    ],
)
def test_compile_from_ast(driver, program, program_inputs):
    ast_program, expected = program

    compiler = Compiler()
    compiler.compile_statement(ast_program())
    asm = compiler.generate_assembly()
    js = assemble(asm)

    for i in program_inputs:
        output, exit_code = run_program_js(driver=driver, desmos_js=js, program_input=i)
        assert exit_code == 0
        assert output == expected(i)
