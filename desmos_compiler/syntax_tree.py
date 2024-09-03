from dataclasses import dataclass
from enum import Enum


def indent(s: str, levels: int = 1):
    return "\n".join(["    " * levels + i for i in s.split("\n")])


@dataclass(frozen=True)
class DesmosType:
    """Type (of a variable, parameter, or function return)"""

    type: str

    def __repr__(self) -> str:
        return self.type


@dataclass(frozen=True)
class FunctionParameter:
    """
    Type and name of function parameter
    """

    var: "Variable"
    type: DesmosType

    def __repr__(self) -> str:
        return f"{self.type} {self.var}"


@dataclass(frozen=True)
class Expression:
    """Any node which can be evaluated"""


@dataclass(frozen=True)
class Literal(Expression):
    """A constant expression"""

    val: str

    def __repr__(self) -> str:
        return self.val


@dataclass(frozen=True)
class Variable(Expression):
    """Variable"""

    name: str

    def __repr__(self) -> str:
        return self.name


class Operator(Enum):
    MULT = "*"
    DIV = "/"
    MOD = "%"

    ADD = "+"
    SUB = "-"

    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="


@dataclass(frozen=True)
class BinaryOperation(Expression):
    """
    Binary operation between values
    """

    arg1: Expression
    arg2: Expression
    op: Operator

    def __repr__(self) -> str:
        return f"({self.arg1} {self.op.value} {self.arg2})"


@dataclass(frozen=True)
class FunctionCall(Expression):
    """
    A call to a function
    """

    name: Variable
    args: list[Expression]

    def __repr__(self) -> str:
        args = ", ".join(str(i) for i in self.args)
        return f"{self.name}( {args} )"


@dataclass(frozen=True)
class Statement:
    """Any node which can be executed"""


@dataclass(frozen=True)
class Group(Statement):
    """Group of multiple statements"""

    statements: list[Statement]

    def __repr__(self) -> str:
        return "\n".join([str(i) for i in self.statements])


@dataclass(frozen=True)
class Declaration(Statement):
    """
    Declare a variable
    """

    var: Variable
    type: DesmosType

    def __repr__(self) -> str:
        return f"{self.type} {self.var};"


@dataclass(frozen=True)
class Assignment(Statement):
    """
    Assign a variable
    """

    var: Variable
    val: Expression

    def __repr__(self) -> str:
        return f"{self.var} = {self.val};"


@dataclass(frozen=True)
class If(Statement):
    """Conditional if / else if / else"""

    condition: Expression
    contents: Statement
    _else: Statement | None

    def __repr__(self) -> str:
        contents = indent(str(self.contents))
        res = f"if ( {self.condition} ){{\n{contents}\n}}"
        if self._else is not None:
            else_contents = indent(str(self._else))
            res += f" else {{\n{else_contents}\n}}"
        return res


@dataclass(frozen=True)
class While(Statement):
    """While loop"""

    condition: Expression
    contents: Statement

    def __repr__(self) -> str:
        contents = indent(str(self.contents))
        res = f"while ( {self.condition} ){{\n{contents}\n}}"
        return res



@dataclass(frozen=True)
class FunctionDefinition(Statement):
    """
    Define a new function
    """

    name: Variable
    ret_type: DesmosType
    params: list[FunctionParameter]
    body: Statement

    def __repr__(self) -> str:
        body = indent(str(self.body))
        args = ", ".join([str(i) for i in self.params])
        res = f"{self.ret_type} {self.name} ( {args} ){{\n{body}\n}}"
        return res


@dataclass(frozen=True)
class FunctionReturn(Statement):
    """
    Return expression from a function
    """

    expr: Expression

    def __repr__(self) -> str:
        return f"return {self.expr};"


@dataclass(frozen=True)
class FunctionCallStatement(Statement):
    """
    A standalone function call
    """
    call: FunctionCall

    def __repr__(self) -> str:
        return f"{self.call};"
