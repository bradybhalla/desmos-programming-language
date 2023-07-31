from typing import Final, NamedTuple
from functools import reduce
from pathlib import Path


class DesmosProgramError(Exception):
    pass

class Action:
    """
    A single desmos action
    """

    def __init__(self, var: str, expr: str):
        self.var: str = var
        self.expr: str = expr

    def __repr__(self):
        return f"{self.var} \\to {self.expr}"

    def __add__(self, other: 'Action|str')->str:
        if other == "":
            return str(self)
        return f"{self},{other}"


def combine_actions(actions: list[Action]):
    return "\\left(" + reduce(lambda x, y: y+x, actions, "") + "\\right)"


class Conditional:
    """
    A desmos conditional statement.
    """

    def __init__(self):
        self.conditions: dict[str, list[Action]] = {}

    def add(self, action: Action, condition: str = "")->None:
        """
        Add an action with a condition to the statement.

        If condition == "", it will be a default action
        """
        if condition not in self.conditions:
            self.conditions[condition] = []

        self.conditions[condition].append(action)

    def __repr__(self):
        terms: list[str] = []
        default: str = ""
        for condition, actions in self.conditions.items():
            action_str = combine_actions(actions)
            if condition == "":
                default = action_str
            else:
                terms.append(f"{condition}:\\left({action_str}\\right)")
        if default != "":
            terms.append(default)
        return "\\left\\{" + ",".join(terms) + "\\right\\}"


class StepProgram:
    def __init__(self):
        self.line_pointer: str = "l"
        self.line_counter: int = 0
        self.ticker: Conditional = Conditional()
        self.ticker.add(Action(self.line_pointer, self.line_pointer), "")

        # varible and its initial value
        self.vars: dict[str, str] = {self.line_pointer: "0"}

    def add_var(self, var: str, initial_value: str)->None:
        """
        Add a variable to the program.

        This must be done so it is initialized in Desmos.
        """
        if var in self.vars:
            raise DesmosProgramError(f"variable '{var}' already exists")
        self.vars[var] = initial_value

    def add_line(self, actions)->int:
        """
        Add a line to the program.  A line consists of 1 or more
        actions which are run when the line pointer is at its
        index.

        Returns the index of the line.
        """
        for i in actions:
            self.ticker.add(i, f"{self.line_pointer}={self.line_counter}")
        self.line_counter += 1
        return self.line_counter-1

    def create_reset_action(self)->str:
        """
        Return a desmos line to reset all variables.
        """
        return "R_{eset}=" + combine_actions([Action(i, j) for i, j in self.vars.items()])

    def create_ticker_action(self)->str:
        """
        Return a desmos line for the main ticker action.
        """
        return "T_{icker}=" + str(self.ticker)

    def create_program(self)->str:
        """
        Return a string which can be pasted into Desmos of the entire program.
        """
        lines: list[str] = []
        lines.append(self.create_reset_action())
        lines.append(self.create_ticker_action())

        for i in self.vars.keys():
            lines.append(f"{i}=-1")

        return "\n".join(lines)


class Stack:
    def __init__(self, stepProg: StepProgram) -> None:
        self.name: str = "S"
        self.pointer_name: str = "S_p"
        self.size: int = 1000
        
        self.prog = stepProg
        self.prog.add_var(self.name, f"\\left[1...{self.size}\\right]*0")
        self.prog.add_var(self.pointer_name, "0")
    def push_action(self):
        pass
    def pop_action(self):
        pass

class Heap:
    def __init__(self, stepProg: StepProgram) -> None:
        self.name: str = "H"
        self.size: int = 1000

        self.prog = stepProg
        self.prog.add_var(self.name, f"\\left[1...{self.size}\\right]*0")
    def alloc_action(self, amount: str):
        pass
        
    def free_action(self, pointer: str):
        pass

if __name__ == "__main__":
    prog = StepProgram()
    stack = Stack(prog)

    prog.add_var("a", "1")
    prog.add_var("b", "2")

    prog.add_line([Action("a", "a+1"), Action("l", "l+1")])
    prog.add_line([Action("a", "a+1"), Action("b", "b+1"), Action("l", "l+1")])
    prog.add_line([Action("l", "l")])
    print(prog.create_program(), end="")
