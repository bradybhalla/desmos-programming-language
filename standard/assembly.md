# Standard for Desmos Assembly

A low level language specifying the structure of the Desmos program. This language contains the following instructions:
- `expr <expression>`: create a Desmos expression.
- `label <label name>`: make a label which can be jumped to from anywhere in the program.
- `line <actions>`: adds a line to the program which runs the actions. Multiple actions are comma separated and every line is responsible for including either a NEXTLINE or GOTO action to move the program counter.

Desmos assembly makes the following substitutions in actions:
- `IN`, `OUT` become the input and output variables, respectively.
- `DONE` becomes the exit code. A non-negative number means the program has exited.
- `LINE` becomes the current line.
- `NEXTLINE` generates an action which moves the program counter to the next line.
- `GOTO <label name>` generates an action moving the program counter to after `<label name>`.
