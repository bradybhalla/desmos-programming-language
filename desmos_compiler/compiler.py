from dataclasses import dataclass
from desmos_compiler.syntax_tree import (
    Assignment,
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
    type: str
    defined: bool
    register: str


class ScopeHandler:
    def __init__(self, prev: "ScopeHandler|None"):
        self.prev = prev
        self.locals: dict[str, VarInfo] = {}
        self.register_count = 0

    def declare_var(self, var: Variable, type: str, register: str | None = None)->str:
        """
        Declare a variable. Returns the register name.
        """
        if var.name in self.locals:
            raise CompilerError(f"Variable {var.name} is already declared")

        if register is None:
            register = f"X_{{{self.register_count}}}"
            self.register_count += 1

        self.locals[var.name] = VarInfo(type, False, register)
        return register

    def var_defined(self, var: Variable):
        if var.name in self.locals:
            self.locals[var.name].defined = True
        else:
            # TODO: this shouldn't be an error
            # as long as we can make sure it is defined in all branches of scopes
            raise CompilerError(f"Variable {var.name} defined in a different scope than its declaration")

    def get_register(self, var: Variable)->str:
        if var.name in self.locals:
            if not self.locals[var.name].defined:
                raise CompilerError(f"Variable {var.name} used before definition")
            return self.locals[var.name].register
        else:
            if self.prev is None:
                raise CompilerError(f"Variable {var.name} used before declaration")
            return self.prev.get_register(var)

    def push_scope(self):
        pass

    def pop_scope(self):
        pass


class Compiler:
    def __init__(self):
        self.scope = ScopeHandler(None)
        self.registers = set()
        self.assembly = ""

        self.label_counter = 0

        # declare required registers
        # these registers are created by the assembler
        self.scope.declare_var(Variable("$IN"),   "num", "IN")
        self.scope.declare_var(Variable("$OUT"),  "num", "OUT")
        self.scope.declare_var(Variable("$DONE"), "num", "DONE")

        self.scope.var_defined(Variable("$IN"))

    def compile_statement(self, statement: Statement):
        if not isinstance(statement, Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(statement, Assignment):
            val = self.compile_node(statement.val)
            if statement.var.name not in self.scope.locals:
                self.registers.add(self.scope.declare_var(statement.var, "num"))
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
        registers = "".join([f"reg {i}\n" for i in self.registers])
        return registers + self.assembly


def compile(program: str) -> str:
    ast_statements = parse(program)

    try:
        compiler = Compiler()
        compiler.compile_statement(ast_statements)
    except CompilerError as e:
        print("Error during compilation:", e)
        return ""

    return compiler.generate_assembly()
