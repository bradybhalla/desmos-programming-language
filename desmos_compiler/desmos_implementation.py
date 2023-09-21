from desmos_compiler.intermediate import (
    Command,
    Condition,
    ConditionalCommand,
    GotoLineCommand,
    IntermediateLineProgram,
    SetRegisterCommand,
)

from json import dumps
from typing import NamedTuple


class RunActionCommand(Command):
    def __init__(self, action):
        self.action = action

    def __repr__(self):
        return f"Run Desmos action {self.action}"

    def get_error(self, _: "IntermediateLineProgram") -> str:
        return ""


class DesmosExpr(NamedTuple):
    id: str
    latex: str
    kwargs: dict[str, str] = {}


class DesmosImplementation:
    """
    Implements `IntermediateLineProgram` in Desmos

    Creates the R_{un} action, but the other required variables
    specified in `standard/desmos.md` must be created as registers.
    """

    LINE_REGISTER = "L_{ine}"

    @staticmethod
    def _latexify_command(command: Command) -> str:
        if isinstance(command, SetRegisterCommand):
            return f"{command.register} \\to {command.value}"
        elif isinstance(command, GotoLineCommand):
            return f"{DesmosImplementation.LINE_REGISTER} \\to {command.line}"
        elif isinstance(command, ConditionalCommand):
            if len(command.conditions) == 1 and command.conditions[0].condition == "":
                return (
                    "\\left("
                    + ", ".join(
                        [
                            DesmosImplementation._latexify_command(cmd)
                            for cmd in command.conditions[0].commands
                        ]
                    )
                    + "\\right)"
                )

            condition_strs = []
            for condition in command.conditions:
                cmds_str = (
                    "\\left("
                    + ", ".join(
                        [
                            DesmosImplementation._latexify_command(cmd)
                            for cmd in condition.commands
                        ]
                    )
                    + "\\right)"
                )

                if condition.condition == "":
                    condition_strs.append(cmds_str)
                else:
                    condition_strs.append(condition.condition + ": " + cmds_str)
            return "\\left\\{" + ", ".join(condition_strs) + "\\right\\}"
        elif isinstance(command, RunActionCommand):
            return command.action
        else:
            raise ValueError(
                f"No Desmos implementation for command of type {type(command).__name__}"
            )

    @staticmethod
    def generate_exprs(prog: IntermediateLineProgram) -> list[DesmosExpr]:
        # ensure there are no errors in the program
        assert prog.get_errors() == ""

        # ensure the program will comply with `standard/desmos.md`
        assert "I_{n}" in prog.registers
        assert "O_{ut}" in prog.registers
        assert "D_{one}" in prog.registers

        res = []

        # create R_{un}
        run_command = ConditionalCommand(
            [
                Condition(
                    f"{DesmosImplementation.LINE_REGISTER} = {i}",
                    [RunActionCommand(f"L_{{ine{i}}}")],
                )
                for i in range(len(prog.lines))
            ]
            + [Condition("", [SetRegisterCommand("D_{one}", "0")])]
        )
        res.append(
            DesmosExpr(
                id="run",
                latex="R_{un} = " + DesmosImplementation._latexify_command(run_command),
            )
        )

        # create special line register
        res.append(
            DesmosExpr(
                id=f"register {DesmosImplementation.LINE_REGISTER}",
                latex=f"{DesmosImplementation.LINE_REGISTER} = 0",
            )
        )

        # initialize registers
        # set ids for special registers
        for name, inital_value in prog.registers.items():
            if name == "I_{n}":
                id = "in"
            elif name == "O_{ut}":
                id = "out"
            elif name == "D_{one}":
                id = "done"
            else:
                id = f"register {name}"

            res.append(DesmosExpr(id=id, latex=f"{name} = {inital_value}"))

        # create lines
        for i, line in enumerate(prog.lines):
            latex = []
            for cmd in line:
                latex.append(DesmosImplementation._latexify_command(cmd))

            res.append(
                DesmosExpr(id=f"line {i}", latex=f"L_{{ine{i}}} = " + ", ".join(latex))
            )

        return res

    @staticmethod
    def generate_js(exprs: list[DesmosExpr]) -> str:
        """
        Convert a list of `DesmosExpr` tuples to javascript code
        which creates the expressions when run in Desmos
        """
        json = dumps([{"id": i.id, "latex": i.latex, **i.kwargs} for i in exprs])
        return f"calculator.setExpressions({json})"
