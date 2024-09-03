import re
from dataclasses import dataclass, field
from json import dumps

# required expressions
RUN = "R_{un}"
IN = "I_{n}"
OUT = "O_{ut}"
DONE = "D_{one}"

# line register
LINE = "L_{ine}"


@dataclass
class DesmosExpr:
    id: str
    latex: str
    kwargs: dict[str, str] = field(default_factory=lambda: dict())


def generate_js(exprs: list[DesmosExpr]) -> str:
    """
    Convert a list of `DesmosExpr` objects to javascript code
    which creates the expressions when run in Desmos
    """
    json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in exprs])
    return f"calculator.setExpressions({json})"


def process_line(line: str, labels: dict[str, str]):
    line = re.sub(r"\bDONE\b", DONE, line)
    line = re.sub(r"\bOUT\b", OUT, line)
    line = re.sub(r"\bIN\b", IN, line)
    line = re.sub(r"\bLINE\b", LINE, line)
    line = re.sub(r"\bNEXTLINE\b", rf"{LINE} \\to {LINE} + 1", line)
    line = re.sub(r"\bGOTO\b (\w+)", lambda g: rf"{LINE} \to {labels[g.group(1)]}", line)
    return line


def assemble(program: str):
    """
    Turn a program written in Desmos assembly into javascript
    """
    lines = []
    exprs = []
    labels = {}

    for line in program.strip().split("\n"):
        if line == "":
            continue

        line_type = re.match(r"^(\w+) ?(.*)$", line.strip())

        assert line_type is not None, f'invalid format of line "{line}"'

        match line_type.group(1):
            case "line":
                lines.append(line_type.group(2))
            case "label":
                labels[line_type.group(2)] = str(len(lines))
            case "expr":
                # TODO: support for kwargs to DesmosExpr
                exprs.append(line_type.group(2))
            case _:
                raise ValueError(f'unknown type of line "{line}"')

    standard_expressions = [
        DesmosExpr("in", f"{IN}=0"),
        DesmosExpr("out", f"{OUT}=0"),
        DesmosExpr("done", f"{DONE}=-1"),
        DesmosExpr("line", f"{LINE}=0"),
    ]
    expr_expressions = [DesmosExpr(f"expr{i}", j) for i, j in enumerate(exprs)]

    lines = [process_line(i, labels) for i in lines]
    run_latex = RUN + r" = \left\{"
    for i, j in enumerate(lines):
        run_latex += rf"{LINE}={i}:\left({j}\right)"
        if i < len(lines) - 1:
            run_latex += ", "
    run_latex += r"\right\}"

    all_expressions = (
        [DesmosExpr("run", run_latex)] + standard_expressions + expr_expressions
    )

    return generate_js(all_expressions)
