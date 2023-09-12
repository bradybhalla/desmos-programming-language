# line program to desmos program

# implement memory, io, etc.

from json import dumps
from typing import NamedTuple


class DesmosExpr(NamedTuple):
    id: str
    latex: str
    kwargs: dict[str, str] = {}


def generate_js(desmos_exprs: list[DesmosExpr]):
    """
    Convert a list of `DesmosExpr` tuples to javascript code
    which creates the expressions when run in Desmos
    """
    json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in desmos_exprs])
    return f"calculator.setExpressions({json})"
