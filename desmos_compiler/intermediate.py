from abc import ABC, abstractmethod
from typing import NamedTuple


class Command(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError

    @abstractmethod
    def get_error(self, line_prog: "IntermediateLineProgram") -> str:
        """
        Returns "" if the command is valid in the context of `line_prog` and
        returns the error otherwise
        """
        raise NotImplementedError


class SetRegisterCommand(Command):
    def __init__(self, register: str, new_value: str):
        self.register = register
        self.value = new_value

    def __repr__(self):
        return f"Set {self.register}={self.value}"

    def get_error(self, line_prog) -> str:
        return (
            ""
            if self.register in line_prog.registers
            else f"Register {self.register} is not initialized"
        )


class GotoLineCommand(Command):
    def __init__(self, line: int):
        self.line = line

    def __repr__(self):
        return f"Goto line {self.line}"

    def get_error(self, _: "IntermediateLineProgram") -> str:
        return ""


class Condition(NamedTuple):
    """
    Stores a condition and a command to be used when the
    condition is satisfied.

    An empty condition should go last and is always satisfied.
    """

    condition: str
    command: Command


class ConditionalCommand(Command):
    def __init__(self, conditions: list[Condition]):
        self.conditions = conditions

    def __repr__(self):
        res = [f"{cond} ? {cmd}" for cond, cmd in self.conditions]
        return "{ " + ", ".join(res) + " }"

    def get_error(self, line_prog) -> str:
        return ", ".join(
            filter(
                lambda x: x != "",
                [cmd.get_error(line_prog) for _, cmd in self.conditions],
            )
        )


class IntermediateLineProgram:
    """
    An intermediate representation of the program
    """

    def __init__(self):
        self.registers: dict[str, str] = {}
        self.lines: list[list[Command]] = []

    def add_register(self, name: str, initial_value: str):
        """
        Add a register to the program.
        """
        if name in self.registers:
            raise ValueError(f"Register {name} already exists")

        self.registers[name] = initial_value

    def add_line(self, commands: list[Command]) -> int:
        """
        Add a line to the program.  A line consists of a list of
        commands which are run when the line pointer is at its
        index.

        Returns the index of the new line.
        """
        self.lines.append(commands)
        return len(commands) - 1

    def __repr__(self):
        res = []

        res.append("REGISTERS:")
        for name, val in self.registers.items():
            res.append(f"{name}={val}")

        res.append("\nLINES:")
        for i, line in enumerate(self.lines):
            line_str = ", ".join([str(c) for c in line])
            res.append(f"{i}) {line_str}")

        return "\n".join(res)

    def get_errors(self) -> str:
        """
        Returns basic errors from each line
        """
        errors = filter(
            lambda x: x[1] != "",
            [
                (line_num, cmd.get_error(self))
                for line_num, line in enumerate(self.lines)
                for cmd in line
            ],
        )

        errors = [f"{line_num}) {error}" for line_num, error in errors]
        return "\n".join(errors)
