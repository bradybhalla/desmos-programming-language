from dataclasses import dataclass
from contextlib import contextmanager
from typing import NamedTuple

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

class ScopeChangeInfo(NamedTuple):
    new_handler: "ScopeHandler"
    asm: str

class ScopeHandler:
    def __init__(self, prev: "ScopeHandler|None", register_lookup: dict[str, str]):
        # TODO: global name lookup
        self.prev = prev
        self.register_lookup = register_lookup
        self.locals: dict[str, VarInfo] = {}

    def declare_var(self, var: Variable, type: DesmosType):
        if var.name in DEFAULT_VARS:
            raise CompilerError(f"Variable {var.name} is a default variable and cannot be declared")
        elif var.name in self.locals:
            raise CompilerError(f"Variable {var.name} is already declared")

        if var.name not in self.register_lookup:
            self.register_lookup[var.name] = f"X_{{{len(self.register_lookup)}}}"

        self.locals[var.name] = VarInfo(type, False)

    def var_defined(self, var: Variable):
        if var.name in self.locals:
            self.locals[var.name].defined = True
        elif self.prev is None:
            raise CompilerError(
                f"Variable {var.name} has not been declared"
            )
        else:
            return self.prev.var_defined(var)

    def is_defined(self, var: Variable):
        if var.name in self.locals:
            return self.locals[var.name].defined
        elif self.prev is None:
            return False
        else:
            return self.prev.is_defined(var)

    def push_scope(self)->ScopeChangeInfo:
        return ScopeChangeInfo(ScopeHandler(self, self.register_lookup), "")

    def pop_scope(self)->ScopeChangeInfo:
        if self.prev is None:
            raise ValueError(f"no scopes left to pop")
        asm = "line NEXTLINE, " + ", ".join([fr"{self.register_lookup[i]} \to C\left({self.register_lookup[i]}\right)" for i in self.locals.keys()]) + "\n"
        return ScopeChangeInfo(self.prev, asm)



HELPER_FUNCTIONS = [
    r"R\left(L_{0},l\right)=\left\{\operatorname{length}\left(L_{0}\right)\le1:\left[l\right],\operatorname{join}\left(L_{0}\left[1...\operatorname{length}\left(L_{0}\right)-1\right],l\right)\right\}",  # replace the last element of L_0 with l
    r"E\left(L_{0}\right)=\operatorname{join}\left(L_{0},\left[0\right]\right)",  # extend the list L_0
    r"C\left(L_{0}\right)=\left\{\operatorname{length}\left(L_{0}\right)=1:\left[\right],L_{0}\left[1...\operatorname{length}\left(L_{0}\right)-1\right]\right\}",  # contract the list L_0
]

DEFAULT_REGISTERS = {"IN", "OUT", "DONE"}
DEFAULT_VARS = {f"${i}" for i in DEFAULT_REGISTERS}


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
            self.scope.locals[f"${i}"] = VarInfo(DesmosType("num"), False)

        self.scope.var_defined(Variable("$IN"))

    @contextmanager
    def _new_scope(self):
        self.scope, asm = self.scope.push_scope()
        self.assembly += asm
        try:
            yield
        finally:
            self.scope, asm = self.scope.pop_scope()
            self.assembly += asm

    def compile_statement(self, statement: Statement):
        if not isinstance(statement, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(statement, Declaration):
            self.scope.declare_var(statement.var, statement.type)
            var = self.register_lookup[statement.var.name]
            self.assembly += fr"line {var} \to E\left({var}\right), NEXTLINE" + "\n"

        elif isinstance(statement, Assignment):
            val = self.compile_node(statement.val)
            self.scope.var_defined(statement.var)
            var = self.register_lookup[statement.var.name]
            if var in DEFAULT_REGISTERS:
                self.assembly += fr"line {var} \to {val}, NEXTLINE" + "\n"
            else:
                self.assembly += fr"line {var} \to R\left({var},{val}\right), NEXTLINE" + "\n"

        elif isinstance(statement, If):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO else{label} \\right\\}}\n"
            with self._new_scope():
                self.compile_statement(statement.contents)

            self.assembly += f"line GOTO endif{label}\n"
            self.assembly += f"label else{label}\n"
            if statement._else is not None:
                with self._new_scope():
                    self.compile_statement(statement._else)
            self.assembly += f"label endif{label}\n"

        elif isinstance(statement, While):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"label begwhile{label}\n"
            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO endwhile{label} \\right\\}}\n"

            with self._new_scope():
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
        """
        Compiles a node. Only works for rvals.
        """
        if not isinstance(node, Node) or isinstance(node, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(node, Literal):
            return node.val
        elif isinstance(node, Variable):
            if node.name not in self.register_lookup:
                raise CompilerError(f"Undeclared variable {node.name}")
            if not self.scope.is_defined(node):
                raise CompilerError(f"Undefined variable {node.name}")
            register = self.register_lookup[node.name]
            if register in DEFAULT_REGISTERS:
                return register
            else:
                return fr"{register}\left[\operatorname{{length}}\left({register}\right)\right]"
        elif isinstance(node, Expression):
            return "".join([self.compile_node(i) for i in node.nodes])
        else:
            raise ValueError("Node cannot be compiled")

    def generate_assembly(self) -> str:
        exprs = "".join([f"expr {i}\n" for i in HELPER_FUNCTIONS])
        exprs += "expr " + ", ".join([fr"{i} \to []" for i in self.register_lookup.values() if i not in DEFAULT_REGISTERS]) + "\n"
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
