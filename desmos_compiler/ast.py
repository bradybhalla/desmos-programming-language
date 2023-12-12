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
        return f"{self.var} = {self.val}"


# class ConditionalExpr(DesmosLiteral):
#     pass


# class If(Node):
#     def __init__(self, condition: ConditionalExpr, contents: list[Statement]):
#         self.condition = condition
#         self.contents = contents

#     def __repr__(self) -> str:
#         contents = indent(str("\n".join([str(i) for i in self.contents])))
#         return f"if ( {self.condition} ){{\n{contents}\n}}"


# class ConditionalGroup(Statement):
#     def __init__(self, ifs: list[If], default: Statement | None):
#         self.ifs = ifs
#         self.default = default

#     def __repr__(self) -> str:
#         res = " else ".join([str(i) for i in self.ifs])
#         if self.default is not None:
#             res += " else {\n" + indent(str(self.default)) + "\n}"
#         return res


class LiteralStatement(Statement):
    def __init__(self, val: Literal):
        self.val = val

    def __repr__(self) -> str:
        return str(self.val)


class Group(Statement):
    def __init__(self, statements: list[Statement]):
        self.statements = statements

    def __repr__(self) -> str:
        return "\n".join(str(self.statements))
