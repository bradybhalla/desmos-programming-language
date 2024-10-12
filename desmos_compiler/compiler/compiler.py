from desmos_compiler.compiler.globals import CURRENT_STACK_BASE_PTR, RETURN_LINES, RETURN_VAL, SIZEOF, STACK, STACK_BASE_PTRS, CompilerError, FuncInfo
from desmos_compiler.compiler.variable_scope import StackVariableScope
from desmos_compiler.syntax_tree import (
    Assignment,
    BinaryOperation,
    Declaration,
    DesmosType,
    Expression,
    FunctionCall,
    FunctionCallStatement,
    FunctionDefinition,
    FunctionReturn,
    Group,
    If,
    Literal,
    Operator,
    Statement,
    Variable,
    While,
)


class Compiler:
    def __init__(self, root: Statement):
        self.root = root
        self.global_scope = StackVariableScope(None, "1")
        self.function_lookup: dict[Variable, FuncInfo] = {}
        self.label_counter = 0

        self.compiling_function = False

        self.program_asm = ""

    def get_binary_op_expr(self, arg1: str, arg2: str, op: Operator):
        """
        Get the desmos expression that results from a binary operation.

        Arguments:
        arg1 -- the first argument as a desmos expression
        arg2 -- the second argument as a desmos expression
        op -- the operator to apply

        Returns a desmos expression that evaluates to the result of the operation.
        """
        match op:
            case Operator.DIV:
                return rf"\left(\frac{{{arg1}}}{{{arg2}}}\right)"
            case Operator.MOD:
                return rf"\operatorname{{mod}}({arg1}, {arg2})"
            case Operator.MULT | Operator.SUB | Operator.ADD:
                op_str = op.value.replace("*", "\\cdot")
                return rf"\left({arg1} {op_str} {arg2}\right)"
            case (
                Operator.EQ
                | Operator.NE
                | Operator.LT
                | Operator.GT
                | Operator.LE
                | Operator.GE
            ):
                op_str = (
                    op.value.replace(">=", "\\ge ")
                    .replace("<=", "\\le")
                    .replace("==", "=")
                )
                return rf"\left\{{{arg1} {op_str} {arg2}:1,0\right\}}"
            case _:
                raise CompilerError(f"Unknown binary operator {op}")


    def eval_expression(self, expr: Expression, scope: StackVariableScope) -> None:
        """
        Evaluate an expression and generate any assembly needed to facilitate this evaluation.

        Places the returned expression in the RETURN_VAL register.
        """
        match expr:
            case Literal(s):
                self.program_asm += f"line {RETURN_VAL} \\to {s}, NEXTLINE\n"
            case Variable(name):
                desmos_expr, var_type = scope.get_var_data_expr(Variable(name))
                if SIZEOF[var_type] == 1:
                    self.program_asm += f"line {RETURN_VAL} \\to {desmos_expr}[1], NEXTLINE\n"
                else:
                    raise CompilerError(f"Variables with size > 1 not yet supported")
            case BinaryOperation(arg1, arg2, op):
                arg_scope = StackVariableScope(scope, scope.get_child_scope_base())

                # evaluate both arguments in a temporary scope
                self.compile_statement(
                    Group(
                        [
                            Declaration(Variable("#arg1"), DesmosType("num")),
                            Assignment(Variable("#arg1"), arg1),
                            Declaration(Variable("#arg2"), DesmosType("num")),
                            Assignment(Variable("#arg2"), arg2),
                        ]
                    ),
                    arg_scope,
                )
                arg1_expr, arg1_type = arg_scope.get_var_data_expr(Variable("#arg1"))
                arg2_expr, arg2_type = arg_scope.get_var_data_expr(Variable("#arg2"))
                if SIZEOF[arg1_type] > 1 or SIZEOF[arg2_type] > 1:
                    raise CompilerError("Variables with size > 1 not yet supported")

                # calculate and save result
                result_expression = self.get_binary_op_expr(arg1_expr + "[1]", arg2_expr + "[1]", op)
                self.program_asm += f"line {RETURN_VAL} \\to {result_expression}, NEXTLINE\n"

                # pop scope
                self.program_asm += arg_scope.pop_scope_asm()

            case FunctionCall(name, args):
                func = self.function_lookup[name]
                if len(args) != len(func.definition.params):
                    raise CompilerError(
                        f"Function {name} expected to have {len(func.definition.params)} arguments"
                    )

                # create temporary scope for calculating arguments (in current context of the program)
                # this will leave arguments on the stack in order
                arg_scope = StackVariableScope(scope, scope.get_child_scope_base())
                for arg_index, (arg, param) in enumerate(
                    zip(args, func.definition.params)
                ):
                    # temporary variable name
                    arg_variable = Variable(f"#arg{arg_index}")

                    # assign temporary variable to argument value
                    self.compile_statement(
                        Declaration(arg_variable, param.type), arg_scope
                    )
                    self.compile_statement(Assignment(arg_variable, arg), arg_scope)

                # set stack frame base pointer to the argument scope's base
                self.program_asm += f"line {STACK_BASE_PTRS}\\to\\operatorname{{join}}\\left({STACK_BASE_PTRS},{arg_scope.get_scope_base()}\\right), NEXTLINE\n"

                # save line location and jump to function
                self.program_asm += f"line {RETURN_LINES}\\to\\operatorname{{join}}\\left({RETURN_LINES},LINE + 1\\right), GOTO {func.goto_label}\n"
            case _:
                raise CompilerError(f"Unknown expression type {type(expr)} ({expr})")


    def compile_statement(
        self, statement: Statement, scope: StackVariableScope
    ) -> None:
        match statement:
            case Group(statements):
                for s in statements:
                    self.compile_statement(s, scope)

            case Declaration(var, var_type):
                self.program_asm += scope.add_var_asm(var, var_type)

            case Assignment(var, val):
                self.eval_expression(val, scope)
                self.program_asm += scope.set_var_asm(var, RETURN_VAL)

            case If(condition, contents, _else):
                label = self.label_counter
                self.label_counter += 1

                self.eval_expression(condition, scope)
                self.program_asm += f"line \\left\\{{{RETURN_VAL} = 1: NEXTLINE, GOTO else{label} \\right\\}}\n"

                new_scope = StackVariableScope(scope, scope.get_child_scope_base())
                self.compile_statement(contents, new_scope)
                self.program_asm += new_scope.pop_scope_asm()

                self.program_asm += f"line GOTO endif{label}\n"
                self.program_asm += f"label else{label}\n"
                if _else is not None:
                    new_scope = StackVariableScope(scope, scope.get_child_scope_base())
                    self.compile_statement(_else, new_scope)
                    self.program_asm += new_scope.pop_scope_asm()

                self.program_asm += f"label endif{label}\n"

            case While(condition, contents):
                label = self.label_counter
                self.label_counter += 1

                self.program_asm += f"label begwhile{label}\n"
                self.eval_expression(statement.condition, scope)
                self.program_asm += f"line \\left\\{{{RETURN_VAL}=1: NEXTLINE, GOTO endwhile{label} \\right\\}}\n"

                new_scope = StackVariableScope(scope, scope.get_child_scope_base())
                self.compile_statement(contents, new_scope)
                self.program_asm += new_scope.pop_scope_asm()

                self.program_asm += f"line GOTO begwhile{label}\n"
                self.program_asm += f"label endwhile{label}\n"

            case FunctionDefinition(name, ret, params, body) as func_def:
                if scope != self.global_scope:
                    raise CompilerError(
                        f"Function {name} cannot be defined because it is not in the global scope"
                    )

                if name in self.function_lookup:
                    raise CompilerError(f"Function {name} is already defined")

                label = f"func{self.label_counter}"
                self.label_counter += 1
                self.function_lookup[name] = FuncInfo(label, func_def)
                # do not generate assembly here because it will go at the end of the program

            case FunctionReturn(expr):
                if not self.compiling_function:
                    raise CompilerError("Return statements must be inside functions")

                self.eval_expression(expr, scope)

                # pop stack frame
                self.program_asm += scope.pop_scope_asm()

                # revert stack frame base pointer
                self.program_asm += f"line {STACK_BASE_PTRS}\\to {STACK_BASE_PTRS}\\left[1...\\operatorname{{length}}\\left({STACK_BASE_PTRS}\\right)-1\\right], NEXTLINE\n"

                # set line to return line number
                self.program_asm += f"line LINE\\to {RETURN_LINES}\\left[\\operatorname{{length}}\\left({RETURN_LINES}\\right)\\right],{RETURN_LINES}\\to {RETURN_LINES}\\left[1...\\operatorname{{length}}\\left({RETURN_LINES}\\right)-1\\right]\n"

            case FunctionCallStatement(call):
                self.eval_expression(call, scope)

            case _:
                raise CompilerError(f"Unknown statement type {type(statement)}")

    def compile_functions(self):
        for info in self.function_lookup.values():
            self.program_asm += f"label {info.goto_label}\n"

            func_scope = StackVariableScope(self.global_scope, CURRENT_STACK_BASE_PTR)

            # arguments should be the top values on the stack
            for p in info.definition.params:
                # ignore assembly output since the values are already on the stack
                _ = func_scope.add_var_asm(p.var, p.type)

            self.compiling_function = True
            self.compile_statement(info.definition.body, func_scope)
            # TODO: what to do with no return
            self.compiling_function = False

    def generate_assembly(self):
        # define global register for the program to use
        global_registers = {
            STACK: "[]",
            STACK_BASE_PTRS: "[-1]",
            RETURN_VAL: "0",
            RETURN_LINES: "[]",
        }
        for i, j in global_registers.items():
            self.program_asm += f"expr {i}={j}\n"

        # create input and output
        self.compile_statement(
            Group(
                [
                    Declaration(Variable("IN"), DesmosType("num")),
                    Assignment(Variable("IN"), Literal("IN")),
                    Declaration(Variable("OUT"), DesmosType("num")),
                ]
            ),
            self.global_scope,
        )

        # generate program assembly
        self.compile_statement(self.root, self.global_scope)

        # set output and exit program
        out_expr, out_type = self.global_scope.get_var_data_expr(Variable("OUT"))
        if SIZEOF[out_type] > 1:
            raise CompilerError("types of size > 1 are not yet supported")
        self.program_asm += f"line OUT \\to {out_expr}[1], DONE \\to 0\n"

        # add function definitions at the end of file
        # so they don't start executing unexpectedly
        self.compile_functions()

        return self.program_asm


def compile_syntax_tree(root: Statement):
    return Compiler(root).generate_assembly()
