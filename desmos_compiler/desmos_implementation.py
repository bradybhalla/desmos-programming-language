from desmos_compiler.intermediate import IntermediateLineProgram

from json import dumps
from typing import NamedTuple


class DesmosExpr(NamedTuple):
    id: str
    latex: str
    kwargs: dict[str, str] = {}


class DesmosImplementation:
    @staticmethod
    def generate_exprs(prog: IntermediateLineProgram) -> list[DesmosExpr]:
        raise NotImplementedError

    @staticmethod
    def generate_js(exprs: list[DesmosExpr]) -> str:
        """
        Convert a list of `DesmosExpr` tuples to javascript code
        which creates the expressions when run in Desmos
        """
        json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in exprs])
        return f"calculator.setExpressions({json})"
