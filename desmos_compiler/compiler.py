import desmos_compiler.ast as ast
from desmos_compiler.parser import parse

class Compiler():
    def __init__(self):
        self.register_map = {}
        self.register_count = 0
        self.assembly = ""

        for var in ["IN", "OUT", "DONE"]:
            self.register_map[var] = var
            # registers are already created by assembler

    def _create_var(self, var: ast.Variable):
        assert var.name not in self.register_map

        self.register_map[var.name] = f"X_{{{self.register_count}}}"
        self.assembly += f"reg {self.register_map[var.name]}\n"
        self.register_count += 1

    def compile_statement(self, statement: ast.Statement):
        if not isinstance(statement, ast.Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(statement, ast.Assignment):
            if statement.var.name not in self.register_map:
                self._create_var(statement.var)

            self.assembly += "line "
            self.assembly += self.compile_node(statement.var)
            self.assembly += r" \to "
            self.assembly += self.compile_node(statement.val)
            self.assembly += ", NEXTLINE"
            self.assembly += "\n"
        elif isinstance(statement, ast.LiteralStatement):
            self.assembly += "expr " + self.compile_node(statement.val)
        elif isinstance(statement, ast.Group):
            for i in statement.statements:
                self.compile_statement(i)
        else:
            raise ValueError("Statement cannot be compiled")

    def compile_node(self, node: ast.Node)->str:
        if not isinstance(node, ast.Node) or isinstance(node, ast.Statement):
            raise ValueError("Input is of the wrong type")

        if isinstance(node, ast.Literal):
            return node.val
        elif isinstance(node, ast.Variable):
            return self.register_map[node.name]
        elif isinstance(node, ast.Expression):
            return "".join([self.compile_node(i) for i in node.nodes])
        else:
            raise ValueError("Node cannot be compiled")

    def generate_assembly(self)->str:
        return self.assembly

def compile(program: str)->str:
    ast_statements = parse(program)

    compiler = Compiler()
    compiler.compile_node(ast_statements)

    return compiler.generate_assembly()


