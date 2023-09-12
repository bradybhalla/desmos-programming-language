# line program to desmos program

# implement memory, io, etc.

from json import dumps
from typing import NamedTuple


class DesmosExpr(NamedTuple):
    id: str
    latex: str
    kwargs: dict[str, str] = {}

def generate_js(desmos_exprs: list[DesmosExpr]):
    json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in desmos_exprs])
    return f"calculator.setExpressions({json})"
