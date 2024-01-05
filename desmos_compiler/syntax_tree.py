from abc import ABC, abstractmethod


def indent(s: str, levels: int = 1):
    return "\n".join(["    " * levels + i for i in s.split("\n")])


class DesmosType:
    def __init__(self, type: str):
        assert type == "num"
        self.type = type

    def __repr__(self) -> str:
        return self.type


class Node(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


class Statement(Node):
    pass


class Literal(Node):
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return self.val


class Variable(Node):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class FunctionCall(Node):
    def __init__(self, name: str, args: "list[Expression]"):
        self.name = name
        self.args = args

    def __repr__(self) -> str:
        args = ", ".join(str(i) for i in self.args)
        return f"{self.name}( {args} )"


class Expression(Node):
    def __init__(self, nodes: list[Literal | Variable | FunctionCall]):
        self.nodes = nodes

    def __repr__(self) -> str:
        return "".join([str(i) for i in self.nodes])


class Declaration(Statement):
    def __init__(self, var: Variable, type: DesmosType):
        self.var = var
        self.type = type

    def __repr__(self) -> str:
        return f"{self.type} {self.var};"


class Assignment(Statement):
    def __init__(self, var: Variable, val: Expression):
        self.var = var
        self.val = val

    def __repr__(self) -> str:
        return f"{self.var} = {self.val};"


class DeclareAssignment(Statement):
    def __init__(self, var: Variable, type: DesmosType, val: Expression):
        self.var = var
        self.type = type
        self.val = val

    def __repr__(self) -> str:
        return f"{self.type} {self.var} = {self.val};"


class If(Statement):
    def __init__(
        self, condition: Expression, contents: Statement, _else: Statement | None
    ):
        self.condition = condition
        self.contents = contents
        self._else = _else

    def __repr__(self) -> str:
        contents = indent(str(self.contents))
        res = f"if ( {self.condition} ){{\n{contents}\n}}"
        if self._else is not None:
            else_contents = indent(str(self._else))
            res += f" else {{\n{else_contents}\n}}"
        return res


class While(Statement):
    def __init__(self, condition: Expression, contents: Statement):
        self.condition = condition
        self.contents = contents

    def __repr__(self) -> str:
        contents = indent(str(self.contents))
        res = f"while ( {self.condition} ){{\n{contents}\n}}"
        return res


class FunctionParameter(Statement):
    def __init__(self, var: Variable, type: DesmosType):
        self.var = var
        self.type = type

    def __repr__(self) -> str:
        return f"{self.type} {self.var}"


class FunctionDefinition(Statement):
    def __init__(
        self,
        name: str,
        ret_type: DesmosType,
        params: list[FunctionParameter],
        body: Statement,
    ):
        self.name = name
        self.ret_type = ret_type
        self.params = params
        self.body = body

    def __repr__(self) -> str:
        body = indent(str(self.body))
        args = ", ".join([str(i) for i in self.params])
        res = f"{self.ret_type} {self.name} ( {args} ){{\n{body}\n}}"
        return res


class LiteralStatement(Statement):
    def __init__(self, val: Literal):
        self.val = val

    def __repr__(self) -> str:
        return str(self.val)


class Group(Statement):
    def __init__(self, statements: list[Statement]):
        self.statements = statements

    def __repr__(self) -> str:
        return "\n".join([str(i) for i in self.statements])
