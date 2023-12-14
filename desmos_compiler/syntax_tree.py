from abc import ABC, abstractmethod


def indent(s: str, levels: int = 1):
    return "\n".join(["    " * levels + i for i in s.split("\n")])


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


class Expression(Node):
    def __init__(self, nodes: list[Literal | Variable]):
        self.nodes = nodes

    def __repr__(self) -> str:
        return "".join([str(i) for i in self.nodes])


class Assignment(Statement):
    def __init__(self, var: Variable, val: Expression):
        self.var = var
        self.val = val

    def __repr__(self) -> str:
        return f"{self.var} = {self.val};"


class If(Statement):
    def __init__(self, condition: Expression, contents: Statement, _else: Statement | None):
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
