from json import dumps
import re
from typing import NamedTuple

# required expressions
RUN = "R_{un}"
IN = "I_{n}"
OUT = "O_{ut}"
DONE = "D_{one}"

# line register
LINE = "L_{ine}"


class DesmosExpr(NamedTuple):
    id: str
    latex: str
    kwargs: dict[str, str] = {}


def generate_js(exprs: list[DesmosExpr]) -> str:
    """
    Convert a list of `DesmosExpr` tuples to javascript code
    which creates the expressions when run in Desmos
    """
    json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in exprs])
    return f"calculator.setExpressions({json})"


def make_substitutions(line: str, labels: dict[str, str]):
    line = re.sub(r"NEXTLINE", lambda _: r"LINE \to LINE + 1", line)
    line = re.sub(r"GOTO (\w+)", lambda g: rf"LINE \to {labels[g.group(1)]}", line)
    line = re.sub(r"LINE", LINE, line)
    line = re.sub(r"DONE", DONE, line)
    line = re.sub(r"OUT", OUT, line)
    line = re.sub(r"IN", IN, line)
    return line


def assemble(program: str):
    """
    Turn a program written in Desmos assembly into javascript
    """
    registers = []
    lines = []
    exprs = []
    labels = {}

    for line in program.strip().split("\n"):
        if line == "":
            continue

        line_type = re.match(r"^(\w+) ?(.*)$", line.strip())
        if line_type is None:
            raise ValueError(f'invalid format of line "{line}"')

        if line_type.group(1) == "reg":
            registers.append(line_type.group(2))

        elif line_type.group(1) == "line":
            val = line_type.group(2)
            lines.append(val)

        elif line_type.group(1) == "label":
            labels[line_type.group(2)] = str(len(lines))

        elif line_type.group(1) == "expr":
            # TODO: support for kwargs to DesmosExpr
            exprs.append(line_type.group(2))

        else:
            raise ValueError(f'unknown type of line "{line}"')

    register_expressions = [
        DesmosExpr("in", f"{IN}=0"),
        DesmosExpr("out", f"{OUT}=0"),
        DesmosExpr("done", f"{DONE}=-1"),
        DesmosExpr("line", f"{LINE}=0"),
    ]
    register_expressions += [
        DesmosExpr(f"reg{i}", f"{make_substitutions(j, labels)}=0")
        for i, j in enumerate(registers)
    ]
    expr_expressions = [
        DesmosExpr(f"expr{i}", make_substitutions(j, labels))
        for i, j in enumerate(exprs)
    ]

    lines = [make_substitutions(i, labels) for i in lines]
    run_latex = RUN + r" = \left\{"
    for i, j in enumerate(lines):
        run_latex += rf"{LINE}={i}:\left({j}\right)"
        if i < len(lines) - 1:
            run_latex += ", "
    run_latex += r"\right\}"

    all_expressions = (
        [DesmosExpr("run", run_latex)] + expr_expressions + register_expressions
    )

    return generate_js(all_expressions)
