from lark import Lark, Transformer, exceptions
from desmos_compiler.syntax_tree import (
    Assignment,
    BinaryOperation,
    Declaration,
    DesmosType,
    FunctionCall,
    FunctionCallStatement,
    FunctionParameter,
    FunctionDefinition,
    FunctionReturn,
    If,
    Literal,
    Group,
    Operator,
    Statement,
    Variable,
    While,
)
from pathlib import Path

# TODO: add -$x with highest priority expr in the grammar


class SyntaxTreeTransformer(Transformer):
    VAR = lambda _, x: Variable(x.value)
    NUM = lambda _, x: Literal(x.value)

    TYPE = lambda _, x: DesmosType(x.value)

    start = lambda _, x: Group(x)

    declaration = lambda _, x: Declaration(x[1], x[0])
    assignment = lambda _, x: Assignment(x[0], x[1])

    if_only = lambda _, x: If(x[0], Group(x[1:]), None)
    else_ = lambda _, x: Group(x)

    def if_else(self, args):
        if_, else_ = args
        return If(if_.condition, if_.contents, else_)

    while_ = lambda _, x: While(x[0], Group(x[1:]))

    function_def = lambda _, x: FunctionDefinition(x[1], x[0], x[2], Group(x[3:]))
    param_list = lambda _, x: x
    func_param = lambda _, x: FunctionParameter(x[1], x[0])

    function_call = lambda _, x: FunctionCall(x[0], x[1])
    arg_list = lambda _, x: x

    function_return = lambda _, x: FunctionReturn(x[0])

    function_call_statement = lambda _, x: FunctionCallStatement(x[0])

    parens_expr = lambda _, x: x[0]
    binary_expr = lambda _, x: BinaryOperation(x[0], x[2], Operator(x[1].value))

class ParserError(Exception):
    pass

def parse(program: str) -> Statement:
    try:
        with open(Path(__file__).resolve().parent / "grammar.lark", "r") as f:
            grammar = f.read()
        l = Lark(grammar, parser="earley")
    except:
        raise ParserError("Could not read grammar file")

    try:
        tree = l.parse(program)
        tree = SyntaxTreeTransformer().transform(tree)
        return tree
    except exceptions.UnexpectedCharacters as e:
        message = f"Unexpected character at line {e.line} col {e.column}"
        message += "\n\n" + e._context
        message += e._format_expected(e.allowed)
        raise ParserError(message)

