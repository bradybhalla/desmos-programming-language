import pytest

from desmos_compiler.intermediate import (
    ConditionalCommand,
    GotoLineCommand,
    IntermediateLineProgram,
    SetRegisterCommand,
    Condition,
)


@pytest.fixture
def program():
    prog = IntermediateLineProgram()
    prog.add_register("s", "2")
    prog.add_line([SetRegisterCommand("a", "1")])
    prog.add_line([SetRegisterCommand("a", "1"), GotoLineCommand(2)])
    prog.add_line(
        [
            ConditionalCommand(
                [
                    Condition("a>1", SetRegisterCommand("a", "1")),
                    Condition(
                        "a=0",
                        ConditionalCommand(
                            [Condition("", SetRegisterCommand("a", "1"))]
                        ),
                    ),
                    Condition("", SetRegisterCommand("a", "1")),
                ]
            )
        ]
    )

    return prog


def test_str(program: IntermediateLineProgram):
    """
    Ensure the string representation of the program is correct. This
    also implies that the registers, lines, and commands were created
    as expected.
    """
    prog_str = str(program)

    expected_str = """
REGISTERS:
s=2

LINES:
0) Set a=1
1) Set a=1, Goto line 2
2) { a>1 ? Set a=1, a=0 ? {  ? Set a=1 },  ? Set a=1 }
    """

    assert prog_str.strip() == expected_str.strip()


def test_errors(program: IntermediateLineProgram):
    """
    Ensure that the expected errors are found and that they go
    away when the necessary changes are made.
    """
    error_str = program.get_errors()

    expected_str = """
0) Register a is not initialized
1) Register a is not initialized
2) Register a is not initialized, Register a is not initialized, Register a is not initialized
    """

    assert error_str.strip() == expected_str.strip()

    # There should be no errors once a is initialized
    program.add_register("a", "0")
    assert program.get_errors() == ""
