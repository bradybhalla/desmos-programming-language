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

HELPER_FUNCTIONS = [
    r"R\left(L_{0},l\right)=\left\{\operatorname{length}\left(L_{0}\right)\le1:\left[l\right],\operatorname{join}\left(L_{0}\left[1...\operatorname{length}\left(L_{0}\right)-1\right],l\right)\right\}",  # replace the last element of L_0 with l
    r"B\left(L_{0},l\right)=\left\{\operatorname{length}\left(L_{0}\right)\le1:\left[l\right],\operatorname{join}\left(l,L_{0}\left[2...\operatorname{length}\left(L_{0}\right)\right]\right)\right\}",  # replace the first element of L_0 with l
    r"E\left(L_{0}\right)=\left\{\operatorname{length}\left(L_{0}\right)=0:\left[0\right],\operatorname{join}\left(L_{0},L_{0}\left[\operatorname{length}\left(L_{0}\right)\right]\right)\right\}",  # extend the list L_0
    r"C\left(L_{0}\right)=\left\{\operatorname{length}\left(L_{0}\right)=1:\left[\right],L_{0}\left[1...\operatorname{length}\left(L_{0}\right)-1\right]\right\}",  # contract the list L_0
]
DEFAULT_REGISTERS = {"IN", "OUT", "DONE"}
DEFAULT_VARS = {f"${i}" for i in DEFAULT_REGISTERS}


class CompilerError(Exception):
    pass


@dataclass
class VarInfo:
    type: DesmosType
    defined: bool


class ScopeHandler:
    def __init__(self, prev: "ScopeHandler|None", register_lookup: dict[str, str]):
        self.prev = prev
        self.register_lookup = register_lookup
        self.locals: dict[str, VarInfo] = {}

    def declare_var(self, var: Variable, type: DesmosType):
        if var.name in DEFAULT_VARS:
            raise CompilerError(
                f"Variable {var.name} is a default variable and cannot be declared"
            )
        elif var.name in self.locals:
            raise CompilerError(f"Variable {var.name} is already declared")

        if var.name not in self.register_lookup:
            self.register_lookup[var.name] = f"X_{{{len(self.register_lookup)}}}"

        self.locals[var.name] = VarInfo(type, False)

    def define_var(self, var: Variable):
        if var.name in self.locals:
            self.locals[var.name].defined = True
        else:
            raise CompilerError(f"Variable {var.name} has not been declared")

    def get_scope(self, var: Variable, function_base: "ScopeHandler")->"Optional[ScopeHandler]":
        if var.name in self.locals:
            return self
        elif self is function_base:
            return None
        elif self.prev is None:
            raise ValueError(f"Something went wrong: function_base never reached in scope search")
        else:
            return self.prev.get_scope(var, function_base)

    def is_defined(self, var: Variable, function_base: "ScopeHandler"):
        scope = self.get_scope(var, function_base)
        return scope is not None and var.name in scope.locals and scope.locals[var.name].defined

    def is_declared(self, var: Variable, function_base: "ScopeHandler"):
        scope = self.get_scope(var, function_base)
        return scope is not None and var.name in scope.locals


class FuncInfo(NamedTuple):
    label: str
    definition: FunctionDefinition


class Compiler:
    def __init__(self):
        self.register_lookup = {}
        self.function_lookup: dict[str, FuncInfo] = {}
        self.scope = ScopeHandler(None, self.register_lookup)
        self.assembly = ""

        self.label_counter = 0
        self.global_scope = self.scope

        # base level scope for the current function
        self._current_function_base = self.scope

        # declare required registers
        # these registers are created by the assembler
        for i in DEFAULT_REGISTERS:
            self.register_lookup[f"${i}"] = i
            self.scope.locals[f"${i}"] = VarInfo(DesmosType("num"), False)

        self.scope.define_var(Variable("$IN"))

    def push_scope(self):
        self.scope = ScopeHandler(self.scope, self.register_lookup)

    def pop_scope(self):
        if self.scope.prev is None:
            raise ValueError(f"no scopes left to pop")

        if len(self.scope.locals) > 0:
            self.assembly += "line NEXTLINE, "
            self.assembly += ", ".join(self.pop_register_stack_asm(i) for i in self.scope.locals.keys())
            self.assembly += "\n"

        self.scope = self.scope.prev

    def push_register_stack_asm(self, variable_name)->str:
        var = self.register_lookup[variable_name]
        return rf"{var} \to E\left({var}\right)"

    def pop_register_stack_asm(self, variable_name)->str:
        reg = self.register_lookup[variable_name]
        return rf"{reg} \to C\left({reg}\right)"

    def set_var(
        self,
        variable: Variable,
        value: str,
        function_base: ScopeHandler,
    ):
        """
        Set the value of a variable. The scope will not extend further than the function base.
        """
        declared_local = self.scope.is_declared(variable, function_base)
        declared_global = self.global_scope.is_declared(variable, self.global_scope)

        if not declared_local and not declared_global:
            raise CompilerError(f"Undeclared variable {variable.name}")

        register = self.register_lookup[variable.name]

        if register in DEFAULT_REGISTERS:
            self.global_scope.define_var(variable)
            return rf"{register} \to {value}"
        elif declared_local:
            var_scope = self.scope.get_scope(variable, function_base)
            assert var_scope is not None
            # TODO: this might not be true if it is defined inside a conditional or while loop
            var_scope.define_var(variable)
            return rf"{register} \to R\left({register},{value}\right)"
        elif declared_global:
            self.global_scope.define_var(variable)
            return rf"{register} \to B\left({register},{value}\right)"

        raise ValueError("This point should not be reached")

    def get_var(self, variable: Variable, function_base: ScopeHandler)->str:
        """
        Returns the value of a variable in Desmos. The scope will not extend further than the function base.
        """
        declared_local = self.scope.is_declared(variable, function_base)
        defined_local = self.scope.is_defined(variable, function_base)
        declared_global = self.global_scope.is_declared(variable, self.global_scope)
        defined_global = self.global_scope.is_defined(variable, self.global_scope)

        if not declared_local and not declared_global:
            raise CompilerError(f"Undeclared variable {variable.name}")

        register = self.register_lookup[variable.name]
        
        if declared_local:
            if defined_local:
                return register if register in DEFAULT_REGISTERS else rf"{register}\left[\operatorname{{length}}\left({register}\right)\right]"
            else:
                raise CompilerError(f"Undefined variable {variable.name}")
        elif declared_global:
            if defined_global:
                return register if register in DEFAULT_REGISTERS else rf"{register}\left[0\right]"
            else:
                raise CompilerError(f"Undefined variable {variable.name}")

        raise ValueError("This point should not be reached")


    def compile_statement(self, statement: Statement):
        if not isinstance(statement, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(statement, Declaration):
            self.scope.declare_var(statement.var, statement.type)
            push_reg = self.push_register_stack_asm(statement.var.name)
            self.assembly += f"line {push_reg}, NEXTLINE\n"

        elif isinstance(statement, Assignment):
            assign = self.set_var(statement.var, self.compile_node(statement.val), self._current_function_base)
            self.assembly += f"line {assign}, NEXTLINE\n"

        elif isinstance(statement, DeclareAssignment):
            # val is evaluated before the variable is declared, so "num $x = $x;" is valid
            val = self.compile_node(statement.val)

            self.scope.declare_var(statement.var, statement.type)
            push_reg = self.push_register_stack_asm(statement.var.name)
            self.assembly += f"line {push_reg}, NEXTLINE\n"

            assign = self.set_var(statement.var, val, self._current_function_base)
            self.assembly += f"line {assign}, NEXTLINE\n"
            

        elif isinstance(statement, If):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO else{label} \\right\\}}\n"

            self.push_scope()
            self.compile_statement(statement.contents)
            self.pop_scope()

            self.assembly += f"line GOTO endif{label}\n"
            self.assembly += f"label else{label}\n"
            if statement._else is not None:
                self.push_scope()
                self.compile_statement(statement._else)
                self.pop_scope()
            self.assembly += f"label endif{label}\n"

        elif isinstance(statement, While):
            label = self.label_counter
            self.label_counter += 1

            self.assembly += f"label begwhile{label}\n"
            self.assembly += f"line \\left\\{{ {self.compile_node(statement.condition)}: NEXTLINE, GOTO endwhile{label} \\right\\}}\n"

            self.push_scope()
            self.compile_statement(statement.contents)
            self.pop_scope()

            self.assembly += f"line GOTO begwhile{label}\n"
            self.assembly += f"label endwhile{label}\n"

        elif isinstance(statement, FunctionCall):
            pass

        elif isinstance(statement, FunctionDefinition):
            pass

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
            return self.get_var(node, self._current_function_base)
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
