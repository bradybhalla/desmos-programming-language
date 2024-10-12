from dataclasses import dataclass

from desmos_compiler.syntax_tree import DesmosType, FunctionDefinition

STACK = "S_{tack}"

# pointers to stack frame bases
STACK_BASE_PTRS = "S_{tackPtrs}"
CURRENT_STACK_BASE_PTR = rf"{STACK_BASE_PTRS}\left[\operatorname{{length}}\left({STACK_BASE_PTRS}\right)\right]"

# register to store return value
RETURN_VAL = "R_{eturnVal}"

# lines to jump back to on "return"
RETURN_LINES = "R_{eturnLines}"

# sizes of variables
SIZEOF = {DesmosType("num"): 1}


class CompilerError(Exception):
    pass


@dataclass
class VarInfo:
    mem_offset: int
    var_type: DesmosType


@dataclass
class FuncInfo:
    goto_label: str
    definition: FunctionDefinition


