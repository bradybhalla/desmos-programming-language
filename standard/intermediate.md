# Intermediate Line Program

- Made up of registers and indexed lines
- The current line is tracked in a special register which we will call `L`
- If there is no `GotoLine` command in a line, the `L` will be incremented
- The program begins on the first line (`L=0`)
- The program exits when `L` does not correspond to an existing line

## Registers
- Registers are global variables.
- The allowed types are numbers and lists.
- Registers don't update until the end of a line.

## Lines
- Each line is a series of commands, which can be one of the following:
    - `SetRegister`: changes the value of a register
    - `GotoLine`: sets the next line to be executed
    - `Conditional`: runs commands based on which condition is met
