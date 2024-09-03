import pytest

from desmos_compiler.parser import parse
from desmos_compiler.syntax_tree import (
    Assignment,
    BinaryOperation,
    Declaration,
    DesmosType,
    FunctionCall,
    FunctionCallStatement,
    FunctionDefinition,
    FunctionParameter,
    FunctionReturn,
    Group,
    If,
    Literal,
    Operator,
    Variable,
    While,
)


def test_var():
    assert parse("num x;\nx=1;") == Group(
        [
            Declaration(Variable("x"), DesmosType("num")),
            Assignment(Variable("x"), Literal("1")),
        ]
    )

    assert parse("num x;\nx=y;") == Group(
        [
            Declaration(Variable("x"), DesmosType("num")),
            Assignment(Variable("x"), Variable("y")),
        ]
    )


@pytest.mark.parametrize("op", Operator)
def test_binary_operation(op):
    assert parse(f"x=x{op.value}1;") == Group(
        [
            Assignment(
                Variable("x"),
                BinaryOperation(Variable("x"), Literal("1"), op),
            )
        ]
    )


def test_order_of_operations():
    assert parse(f"x = (1-2*x)/1 >= 1 % 2;") == Group(
        [
            Assignment(
                Variable("x"),
                BinaryOperation(
                    BinaryOperation(
                        BinaryOperation(
                            Literal("1"),
                            BinaryOperation(Literal("2"), Variable("x"), Operator.MULT),
                            Operator.SUB,
                        ),
                        Literal("1"),
                        Operator.DIV,
                    ),
                    BinaryOperation(Literal("1"), Literal("2"), Operator.MOD),
                    Operator.GE,
                ),
            )
        ]
    )


def test_conditional():
    assert parse("if (x < 2){}") == Group(
        [If(BinaryOperation(Variable("x"), Literal("2"), Operator.LT), Group([]), None)]
    )

    assert parse("if (x < 2){}else if (x < 5) {} else {x=1;}") == Group(
        [
            If(
                BinaryOperation(Variable("x"), Literal("2"), Operator.LT),
                Group([]),
                If(
                    BinaryOperation(Variable("x"), Literal("5"), Operator.LT),
                    Group([]),
                    Group([Assignment(Variable("x"), Literal("1"))]),
                ),
            )
        ]
    )


def test_while():
    assert parse("while (x < 2){x = 2;}") == Group(
        [
            While(
                BinaryOperation(Variable("x"), Literal("2"), Operator.LT),
                Group([Assignment(Variable("x"), Literal("2"))]),
            )
        ]
    )


def test_function():
    assert parse("num add(num x, num y){ return x+y; }") == Group(
        [
            FunctionDefinition(
                Variable("add"),
                DesmosType("num"),
                [
                    FunctionParameter(Variable("x"), DesmosType("num")),
                    FunctionParameter(Variable("y"), DesmosType("num")),
                ],
                Group(
                    [
                        FunctionReturn(
                            BinaryOperation(Variable("x"), Variable("y"), Operator.ADD)
                        )
                    ]
                ),
            )
        ]
    )

    assert parse("x=add(x, 1);") == Group(
        [
            Assignment(
                Variable("x"),
                FunctionCall(Variable("add"), [Variable("x"), Literal("1")]),
            )
        ]
    )

    assert parse("add(x, 1);") == Group(
        [
            FunctionCallStatement(
                FunctionCall(Variable("add"), [Variable("x"), Literal("1")])
            )
        ]
    )
