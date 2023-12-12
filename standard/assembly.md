# Desmos Assembly

A low level language specifying the structure of the Desmos program. Each line is of the form `<type> <data>`

The following types of lines are permitted:
- `reg <name>`: Creates a variable with name `<name>`.
- `line <action>`: Adds a line to the program. `<action>` specifies what happens when the line is executed.
- `label <name>`: Creates a label which can be jumped to from anywhere in the program.
- `expr <expression>`: Creates the expression `<expression>`.

Desmos assembly makes the following substitutions:
- `IN`, `OUT` become the input and output variables, respectively.
- `DONE` becomes the exit code. A non-negative number means the program has exited.
- `GOTO <label>` generates an action making the next executed line be the one after `<label>`.
- `NEXTLINE` generates an action making the next executed line be the following line.
- `LINE` becomes a variable representing the line index.
