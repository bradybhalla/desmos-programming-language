from lark import Lark, Transformer, Tree
from desmos_compiler.syntax_tree import (
    Assignment,
    Expression,
    If,
    Literal,
    Group,
    Variable,
    While,
)

# TODO: add -$x with highest priority expr
GRAMMAR = r"""
start: statement+

?statement: assignment | if_ | while_

lval: VAR
assignment: lval "=" expr ";"

?if_: if_only | if_else
if_only: "if" "(" expr ")" "{" statement+ "}"
if_else: if_only (elif | else_)
?elif: "else" if_
else_: "else" "{" statement+ "}"

while_: "while" "(" expr ")" "{" statement+ "}"

?expr: expr0
?expr0: expr1
      | expr0 (EQ | NE | LT | GT | LE | GE) expr1

?expr1: expr2
      | expr1 (ADD | SUB) expr2

?expr2: expr3
      | expr2 (MULT | DIV | MOD) expr3

?expr3: NUM | VAR
      | "(" expr0 ")" -> parens_expr


VAR: "$" CNAME
NUM: SIGNED_NUMBER

MULT: "*"
DIV: "/"
MOD: "%"

ADD: "+"
SUB: "-"

EQ: "=="
NE: "!="
LT: "<"
GT: ">"
LE: "<="
GE: ">="

%import common.SIGNED_NUMBER
%import common.CNAME
%import common.WS

%ignore WS
"""


class SyntaxTreeTransformer(Transformer):
    VAR = lambda _, x: Expression([Variable(x)])
    NUM = lambda _, x: Expression([Literal(x)])

    start = lambda _, x: Group(x)

    lval = lambda _, x: x[0].nodes[0]
    assignment = lambda _, x: Assignment(x[0], x[1])

    if_only = lambda _, x: If(x[0], Group(x[1:]), None)
    else_ = lambda _, x: Group(x)

    while_ = lambda _, x: While(x[0], Group(x[1:]))

    parens_expr = lambda _, x: _construct(["(", x[0], ")"])

    def __default__(self, data, children, meta):
        if "expr" in data:
            l = children[0]
            op = children[1].value
            r = children[2]
            return get_expression_from_op(op, l, r)
        return Tree(data, children, meta)

    def if_else(self, args):
        if_, else_ = args
        if_._else = else_
        return if_


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
    l = Lark(GRAMMAR, parser="earley")
    tree = l.parse(program)
    tree = SyntaxTreeTransformer().transform(tree)
    return tree
