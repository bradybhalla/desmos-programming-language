# Compiles AST to intermediate line program

from desmos_compiler.ast import (
    Assignment,
    ConditionalExpr,
    ConditionalGroup,
    DesmosLiteral,
    If,
    Node,
    Program,
    Statement,
    Variable,
)
from desmos_compiler.intermediate_line_program import (
    Condition,
    ConditionalCommand,
    GotoLineCommand,
    IntermediateLineProgram,
    SetRegisterCommand,
)

# nodes that are lines by themselves
# assignment, ConditionalGroup


class IntermediateLineProgramCompiler:
    def __init__(self, program: Program) -> None:
        self.program = program
        self.intermediate_program: IntermediateLineProgram = IntermediateLineProgram()

    def _add_statement(self, statement: Statement):
        if not isinstance(statement, Statement):
            raise ValueError(statement, " is not a Statement")

        match statement:
            case Assignment(var=ast_var, val=ast_val):
                name = self._node_to_intermediate_str(ast_var)
                val = self._node_to_intermediate_str(ast_val)
                if name not in self.intermediate_program.registers:
                    self.intermediate_program.add_register(name, "00")
                self.intermediate_program.add_line(
                    [
                        SetRegisterCommand(name, val),
                        self.intermediate_program.goto_next_line_command(),
                    ]
                )
            case ConditionalGroup(ifs=ifs, default=default):
                # this will be updated with commands to jump to each branch
                conditional_line = []
                self.intermediate_program.add_line(conditional_line)

                # this command is used to jump to the end of the conditional
                final_goto = GotoLineCommand(-1)

                # (condition, line)
                goto_condition_cmds: list[tuple[str, GotoLineCommand]] = []

                for i in ifs:
                    # track the condition and the command used to jump to the line
                    goto_condition_cmds.append(
                        (
                            self._node_to_intermediate_str(i.condition),
                            GotoLineCommand(
                                self.intermediate_program.next_line_index()
                            ),
                        )
                    )

                    # compile the branch of the conditional and add to the line program
                    for statement in i.contents:
                        self._add_statement(statement)

                    # jump to the end of the conditional once the branch is complete
                    self.intermediate_program.add_line([final_goto])

                if default is not None:
                    goto_condition_cmds.append(
                        (
                            "",
                            GotoLineCommand(
                                self.intermediate_program.next_line_index()
                            ),
                        )
                    )
                    self._add_statement(default)
                    self.intermediate_program.add_line([final_goto])
                else:
                    goto_condition_cmds.append(("", final_goto))

                conditions = [Condition(i, [j]) for i, j in goto_condition_cmds]
                conditional_line.append(ConditionalCommand(conditions))

                final_goto.line = self.intermediate_program.next_line_index()

            case _:
                raise NotImplementedError(
                    f"statement of type {type(statement).__name__} is not matched"
                )

    def _node_to_intermediate_str(self, node: Node) -> str:
        match node:
            case ConditionalExpr(val=val):
                return val
            case Variable(name=name):
                return name
            case DesmosLiteral(val=val):
                return val
            case _:
                raise NotImplementedError(
                    f"node of type {type(node).__name__} is not matched"
                )

    def compile(self) -> IntermediateLineProgram:
        self.intermediate_program = IntermediateLineProgram()
        self.intermediate_program.add_register("I_{n}", "0")
        self.intermediate_program.add_register("O_{ut}", "0")
        self.intermediate_program.add_register("D_{one}", "-1")

        for node in self.program.ast:
            self._add_statement(node)

        return self.intermediate_program

