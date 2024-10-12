from desmos_compiler.syntax_tree import Assignment, BinaryOperation, Declaration, DirectExpression, Expression, FunctionCall, FunctionCallStatement, FunctionDefinition, FunctionReturn, Group, Statement, Variable, While, Literal, If

def wrap_direct_expression(e: Expression) -> Expression:
    # match all expressions here
    match e:
        case Literal() as l:
            return DirectExpression(l)

        case Variable() as v:
            return DirectExpression(v)

        case BinaryOperation(arg1, arg2, op) as bo:
            wrapped1 = wrap_direct_expression(arg1)
            wrapped2 = wrap_direct_expression(arg2)
            match (wrapped1, wrapped2):
                case DirectExpression(), DirectExpression():
                    return DirectExpression(bo)
                case _:
                    return bo

        case FunctionCall(name, args):
            wrap_args = [wrap_direct_expression(i) for i in args]
            return FunctionCall(name, wrap_args)

        case _:
            raise ValueError("should not have DirectBinaryExpression before wrapping. Make sure to only call this function once.")
        


def perform_all_optimizations(statement: Statement) -> Statement:
    match statement:
        case Group(statements):
            return Group([perform_all_optimizations(i) for i in statements])
        case Declaration() as d:
            return d
        case Assignment(var, val):
            return Assignment(var, wrap_direct_expression(val))
        case If(cond, contents, else_):
            new_cond = wrap_direct_expression(cond)
            new_contents = perform_all_optimizations(contents)
            new_else = perform_all_optimizations(else_) if else_ is not None else None
            return If(new_cond, new_contents, new_else)
        case While(cond, contents):
            new_cond = wrap_direct_expression(cond)
            new_contents = perform_all_optimizations(contents)
            return While(new_cond, new_contents)
        case FunctionDefinition() as fd:
            return fd
        case FunctionReturn(ret):
            return FunctionReturn(wrap_direct_expression(ret))
        case FunctionCallStatement(call):
            wrapped_call = wrap_direct_expression(call)
            assert isinstance(wrapped_call, FunctionCall), "wrapping direct expression should return a function call here"
            return FunctionCallStatement(wrapped_call)
        case _:
            raise ValueError("unknown statement type ", type(statement))


