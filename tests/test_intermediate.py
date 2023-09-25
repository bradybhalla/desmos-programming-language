import pytest

from desmos_compiler.intermediate_line_program import (
    ConditionalCommand,
    GotoLineCommand,
    IntermediateLineProgram,
    SetRegisterCommand,
    Condition,
)


@pytest.fixture
def broken_program():
    """
    An intermediate program with multiple issues
    """
    prog = IntermediateLineProgram()
    prog.add_register("s", "2")
    prog.add_line([SetRegisterCommand("a", "1")])
    prog.add_line([SetRegisterCommand("a", "1"), GotoLineCommand(2)])
    prog.add_line(
        [
            ConditionalCommand(
                [
                    Condition("a>1", [SetRegisterCommand("a", "1")]),
                    Condition(
                        "a=0",
                        [
                            ConditionalCommand(
                                [Condition("", [SetRegisterCommand("a", "1")])]
                            )
                        ],
                    ),
                    Condition("", [SetRegisterCommand("a", "1")]),
                ]
            )
        ]
    )
    prog.add_line([ConditionalCommand([]), ConditionalCommand([Condition("", [])])])

    return prog


def test_str(broken_program: IntermediateLineProgram):
    """
    Ensure the string representation of the program is correct. This
    also implies that the registers, lines, and commands were created
    as expected.
    """
    prog_str = str(broken_program)

    expected_str = """
REGISTERS:
s=2

LINES:
0) Set a=1
1) Set a=1, Goto line 2
2) { a>1 ? [Set a=1], a=0 ? [{  ? [Set a=1] }],  ? [Set a=1] }
3) {  }, {  ? [] }
    """

    assert prog_str.strip() == expected_str.strip()


def test_errors(broken_program: IntermediateLineProgram):
    """
    Ensure that the expected errors are found and that they go
    away when the necessary changes are made.
    """
    error_str = broken_program.get_errors()

    expected_str = """
0) Register a is not initialized
1) Register a is not initialized
2) Register a is not initialized, Register a is not initialized, Register a is not initialized
3) There must be at least one condition
3) Conditions must have at least one command
    """

    assert error_str.strip() == expected_str.strip()

    # There should be no errors after they are fixed
    broken_program.add_register("a", "0")
    [cond1, cond2] = broken_program.lines[3]
    cond1.conditions.append(Condition("", [GotoLineCommand(2)]))  # pyright: ignore
    cond2.conditions[0].commands.append(GotoLineCommand(2))  # pyright: ignore

    assert broken_program.get_errors() == ""
