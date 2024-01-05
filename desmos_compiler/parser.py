from lark import Lark, Transformer
from desmos_compiler.syntax_tree import (
    Assignment,
    Declaration,
    DeclareAssignment,
    DesmosType,
    Expression,
    FunctionCall,
    FunctionParameter,
    FunctionDefinition,
    If,
    Literal,
    Group,
    Variable,
    While,
)
from pathlib import Path

# TODO: add -$x with highest priority expr in the grammar


class SyntaxTreeTransformer(Transformer):
    VAR = lambda _, x: Expression([Variable(x.value)])
    NUM = lambda _, x: Expression([Literal(x.value)])

    FUNC_NAME = lambda _, x: x.value

    TYPE = lambda _, x: DesmosType(x.value)

    start = lambda _, x: Group(x)

    lval = lambda _, x: x[0].nodes[0]
    declare = lambda _, x: Declaration(x[1], x[0])
    assign = lambda _, x: Assignment(x[0], x[1])
    declare_assign = lambda _, x: DeclareAssignment(x[1], x[0], x[2])

    if_only = lambda _, x: If(x[0], Group(x[1:]), None)
    else_ = lambda _, x: Group(x)

    def if_else(self, args):
        if_, else_ = args
        if_._else = else_
        return if_

    while_ = lambda _, x: While(x[0], Group(x[1:]))

    func_param = lambda _, x: FunctionParameter(x[1], x[0])
    param_list = lambda _, x: x
    function_def = lambda _, x: FunctionDefinition(x[1], x[0], x[2], Group(x[3:]))

    arg_list = lambda _, x: x
    function_call = lambda _, x: FunctionCall(x[0], x[1])

    parens_expr = lambda _, x: _construct(["(", x[0], ")"])
    expr = lambda _, x: get_expression_from_op(x[1].value, x[0], x[2])


def _construct(lst: list[Expression | str]):
    expr_list = []
    for i in lst:
        if isinstance(i, Expression):
            expr_list += i.nodes
        elif isinstance(i, str):
            s = i.replace("(", "\\left(").replace(")", "\\right)")
            expr_list.append(Literal(s))
        else:
            raise ValueError("Must be Expression or str")
    return Expression(expr_list)


def get_expression_from_op(op: str, left: Expression, right: Expression):
    if op == "/":
        return _construct(["\\frac{", left, "}{", right, "}"])
    elif op == "%":
        return _construct(["\\operatorname{mod}(", left, ",", right, ")"])
    elif op in "*-+":
        op = op.replace("*", "\\cdot ")
        return _construct([left, op, right])
    elif op == "!=":
        return _construct(["\\left|", left, "- (", right, ")\\right| > 0"])
    elif op in ["<", ">", "<=", ">=", "=="]:
        op = op.replace(">=", "\\ge ")
        op = op.replace("<=", "\\le ")
        op = op.replace("==", " = ")
        return _construct([left, op, right])
    else:
        raise ValueError("unknown operator")


def parse(program: str):
    with open(Path(__file__).resolve().parent / "grammar.lark", "r") as f:
        grammar = f.read()

    l = Lark(grammar, parser="earley")
    tree = l.parse(program)
    tree = SyntaxTreeTransformer().transform(tree)
    return tree
