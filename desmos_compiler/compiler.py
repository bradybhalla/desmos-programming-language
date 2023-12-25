from dataclasses import dataclass

from lark import exceptions
from desmos_compiler.syntax_tree import (
    Assignment,
    Declaration,
    DesmosType,
    Expression,
    Group,
    If,
    Literal,
    LiteralStatement,
    Node,
    Statement,
    Variable,
    While,
)
from desmos_compiler.parser import parse


class CompilerError(Exception):
    pass


@dataclass
class VarInfo:
    type: DesmosType
    defined: bool


class ScopeHandler:
    def __init__(self, prev: "ScopeHandler|None", register_lookup: dict[str, str]):
        # TODO: global name lookup
        self.prev = prev
        self.register_lookup = register_lookup
        self.locals: dict[str, VarInfo] = {}

    def declare_var(self, var: Variable, type: DesmosType):
        if var.name in self.locals:
            raise CompilerError(f"Variable {var.name} is already declared")

        if var.name not in self.register_lookup:
            self.register_lookup[var.name] = f"X_{{{len(self.register_lookup)}}}"

        self.locals[var.name] = VarInfo(type, False)

    def var_defined(self, var: Variable):
        if var.name in self.locals:
            self.locals[var.name].defined = True
        elif var.name in self.register_lookup:
            # TODO: this shouldn't be an error
            # as long as we can make sure it is defined in all branches of scopes
            raise CompilerError(
                f"Variable {var.name} defined in a different scope than its declaration"
            )
        else:
            raise CompilerError(f"Variable {var.name} defined before declaration")

    def get_register(self, var: Variable) -> str:
        if var.name in self.locals:
            if not self.locals[var.name].defined:
                raise CompilerError(f"Variable {var.name} used before definition")
            return self.register_lookup[var.name]
        else:
            if self.prev is None:
                raise CompilerError(f"Variable {var.name} used before declaration")
            return self.prev.get_register(var)

    def push_scope(self):
        pass

    def pop_scope(self):
        pass


HELPER_FUNCTIONS = [
    r"R\left(L,l\right)=\left\{\operatorname{length}\left(L\right)\le1:\left[l\right],\operatorname{join}\left(L\left[1...\operatorname{length}\left(L\right)-1\right],l\right)\right\}",  # replace the last element of L with l
]

DEFAULT_REGISTERS = {"IN", "OUT", "DONE"}


class Compiler:
    def __init__(self):
        self.register_lookup = {}
        self.scope = ScopeHandler(None, self.register_lookup)
        self.assembly = ""

        self.label_counter = 0

        # declare required registers
        # these registers are created by the assembler
        for i in DEFAULT_REGISTERS:
            self.register_lookup[f"${i}"] = i
            self.scope.declare_var(Variable(f"${i}"), DesmosType("num"))

        self.scope.var_defined(Variable("$IN"))

    def compile_statement(self, statement: Statement):
        if not isinstance(statement, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(statement, Declaration):
            self.scope.declare_var(statement.var, statement.type)

        elif isinstance(statement, Assignment):
            val = self.compile_node(statement.val)
            self.scope.var_defined(statement.var)
            var = self.compile_node(statement.var)

            self.assembly += "line "
            self.assembly += var
            self.assembly += r" \to "
            self.assembly += val
            self.assembly += ", NEXTLINE"
            self.assembly += "\n"

        elif isinstance(statement, If):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO else{label} \\right\\}}\n"
            self.compile_statement(statement.contents)
            self.assembly += f"line GOTO endif{label}\n"
            self.assembly += f"label else{label}\n"
            if statement._else is not None:
                self.compile_statement(statement._else)
            self.assembly += f"label endif{label}\n"

        elif isinstance(statement, While):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"label begwhile{label}\n"
            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO endwhile{label} \\right\\}}\n"
            self.compile_statement(statement.contents)
            self.assembly += f"line GOTO begwhile{label}\n"
            self.assembly += f"label endwhile{label}\n"

        elif isinstance(statement, LiteralStatement):
            self.assembly += "expr " + self.compile_node(statement.val)
        elif isinstance(statement, Group):
            for i in statement.statements:
                self.compile_statement(i)
        else:
            raise ValueError("Statement cannot be compiled")

    def compile_node(self, node: Node) -> str:
        if not isinstance(node, Node) or isinstance(node, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(node, Literal):
            return node.val
        elif isinstance(node, Variable):
            return self.scope.get_register(node)
        elif isinstance(node, Expression):
            return "".join([self.compile_node(i) for i in node.nodes])
        else:
            raise ValueError("Node cannot be compiled")

    def generate_assembly(self) -> str:
        exprs = "".join([f"expr {i}\n" for i in HELPER_FUNCTIONS])
        registers = "".join(
            [
                f"reg {i}\n"
                for i in self.register_lookup.values()
                if i not in DEFAULT_REGISTERS
            ]
        )
        return exprs + registers + self.assembly


def compile(program: str) -> str:
    try:
        ast_statements = parse(program)
    except exceptions.UnexpectedCharacters as e:
        message = f"Unexpected character at line {e.line} col {e.column}"
        message += "\n\n" + e._context
        message += e._format_expected(e.allowed)
        print("Syntax Error:", message)
        return ""

    try:
        compiler = Compiler()
        compiler.compile_statement(ast_statements)
    except CompilerError as e:
        print("Error during compilation:", e)
        return ""

    return compiler.generate_assembly()
