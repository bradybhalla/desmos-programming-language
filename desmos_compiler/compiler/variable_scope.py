from desmos_compiler.syntax_tree import Variable, DesmosType

from desmos_compiler.compiler.globals import VarInfo, STACK, SIZEOF, CompilerError

class StackVariableScope:
    def __init__(self, parent: "StackVariableScope | None", variable_scope_base: str):
        self._parent_scope = parent
        self._variable_scope_base = variable_scope_base
        self._var_lookup: dict[Variable, VarInfo] = {}
        self._total_offset = 0

    def get_child_scope_base(self):
        return f"{self._variable_scope_base} + {self._total_offset}"

    def get_scope_base(self):
        return self._variable_scope_base

    def add_var_asm(self, var: Variable, var_type: DesmosType, initial_value_expr: str | None = None):
        """
        Returns desmos assembly which adds a variable to the stack.
        """
        if var in self._var_lookup:
            raise CompilerError(f"Variable {var} is already declared")

        if initial_value_expr is None:
            initial_value_expr = f"\\left[1...{SIZEOF[var_type]}\\right]\\cdot0"

        self._var_lookup[var] = VarInfo(self._total_offset, var_type)
        self._total_offset += SIZEOF[var_type]

        return f"line {STACK}\\to\\operatorname{{join}}\\left({STACK},{initial_value_expr}\\right), NEXTLINE\n"

    def get_var_data_expr(self, var: Variable) -> tuple[str, DesmosType]:
        """
        Get a desmos expression for the variable data.

        Returns:
        expr -- a desmos expression which evaluates to a list containing the data
        type -- a DesmosType of the variable
        """
        if not var in self._var_lookup:
            if self._parent_scope is not None:
                return self._parent_scope.get_var_data_expr(var)
            else:
                raise CompilerError(f"Variable {var} is not in scope")

        offset = self._var_lookup[var].mem_offset
        var_type = self._var_lookup[var].var_type
        slice_start = f"{self._variable_scope_base} + {offset}"
        slice_end = f"{self._variable_scope_base} + {offset} + {SIZEOF[var_type] - 1}"
        return f"{STACK}[{slice_start} ... {slice_end}]", var_type

    @staticmethod
    def _set_var_expr(start, end, expr):
        return (
            rf"\operatorname{{join}}\left(\left\{{{start}=1:\left[\right]"
            + rf",{STACK}\left[1...{start}-1\right]\right\}},{expr},\left"
            + rf"\{{{end}=\operatorname{{length}}\left({STACK}\right):\left"
            + rf"[\right],{STACK}\left[{end}+1...\right]\right\}}\right)"
        )

    def set_var_asm(self, var: Variable, desmos_expr: str) -> str:
        if not var in self._var_lookup:
            if self._parent_scope is not None:
                return self._parent_scope.set_var_asm(var, desmos_expr)
            else:
                raise CompilerError(f"Variable {var} is not in scope")

        offset = self._var_lookup[var].mem_offset
        var_type = self._var_lookup[var].var_type
        slice_start = f"{self._variable_scope_base} + {offset}"
        slice_end = f"{self._variable_scope_base} + {offset} + {SIZEOF[var_type] - 1}"
        new_stack_expr = self._set_var_expr(slice_start, slice_end, desmos_expr)
        return f"line {STACK} \\to {new_stack_expr}, NEXTLINE\n"

    def pop_scope_asm(self) -> str:
        base = self._variable_scope_base
        return (
            f"line {STACK} \\to \\left\\{{{base}=1:\\left[\\right],"
            + f"{STACK}\\left[1...{base}-1\\right]\\right\\}}, NEXTLINE\n"
        )
