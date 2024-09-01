from dataclasses import dataclass
from typing import NamedTuple, Optional

from lark import exceptions
from desmos_compiler.syntax_tree import (
    Assignment,
    Declaration,
    DeclareAssignment,
    DesmosType,
    Expression,
    FunctionCall,
    FunctionDefinition,
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

DEFAULT_REGISTERS = {"IN", "OUT", "DONE"}
DEFAULT_VARS = {f"{i}" for i in DEFAULT_REGISTERS}

# =prev_base is
SIZEOF = {
    "num": 1,
    "addr": 1
}

class CompilerError(Exception):
    pass


@dataclass
class VarInfo:
    size: int
    offset: int

class Context:
    def __init__(self, parent):
        self.parent = parent
        self.vars: dict[str,VarInfo] = {}
        self.vars["#prev_base"] = VarInfo(SIZEOF["addr"], 0)

    def add_var(self, name, type: DesmosType):
        assert name not in self.vars
        total_offset = sum([i.size for i in self.vars.values()])
        self.vars[name] = VarInfo(SIZEOF[type.type], total_offset)


class Compiler:
    def __init__(self, src: Statement):
        self.src = src
        self.assembly = ""
        self.compiled = False

        self.context = Context(None)
        # TODO: define global vars

    def _transform_code(self, statement):
        """
        Any necessary simplifications
        """
        print(statement)


    def _build_assembly(self):
        """
        Define registers, turn statements to assembly
        """
        self.assembly = self._compile_statement(self.src, self.context)
        # TODO: registers


    def _compile_lval(self, expr: Expression, context: Context) -> str:
        pass

    def _compile_rval(self, expr: Expression, context: Context) -> str:
        pass

    def _compile_statement(self, statement, context: Context) -> str:
        pass

    def compile(self):
        self.src = self._transform_code(self.src)
        self._build_assembly()
        self.compiled = True

    def output_assembly(self):
        assert self.compiled
        return self.assembly





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
        compiler = Compiler(ast_statements)
        compiler.compile()
    except CompilerError as e:
        print("Error during compilation:", e)
        return ""

    return compiler.output_assembly()
