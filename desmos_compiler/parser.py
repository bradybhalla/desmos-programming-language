from lark import Lark, ParseTree, Token
from desmos_compiler.syntax_tree import (
    Assignment,
    Expression,
    If,
    Literal,
    Statement,
    Group,
    Variable,
)

GRAMMAR = r"""
start: statement+

statement: assignment | if

assignment: VAR "=" expr ";"

if: if_only | if_else
if_only: "if" "(" expr ")" "{" statement+ "}"
if_else: if_only (elif | else)
elif: "else" if
else: "else" "{" statement+ "}"

expr: (VAR | LITERAL)+

VAR: "$" /[a-zA-Z_][\w_]*/
LITERAL: /1+/

// expr: "(" expr ")" | expr (OP | BOOL_OP) expr | NUM | VAR
// VAR: "$" /[\w_][\w\d_]*/
// NUM: /-?[\d\.]+/
// 
// EQ.1: "=="
// LT.1: "<"
// GT.1: ">"
// LE.1: "<="
// GE.1: ">="
// MULT.2: "*"
// DIV.2: "/"
// ADD.3: "+"
// SUB.3: "-"
// 
// OP: MULT | DIV | ADD | SUB
// BOOL_OP: EQ | LT | GT | LE | GE

%ignore " "
%ignore "\n"
"""

# remove $ from variable
def get_variable_name(var):
    return var[1:]

def parse_expr(tree_node):
    expression_list = []
    for i in tree_node.children:
        if isinstance(i, Token):
            if i.type == "VAR":
                expression_list.append(Variable(i.value))
            elif i.type == "LITERAL":
                expression_list.append(Literal(i.value))
        else:
            raise ValueError("not a token")

    return Expression(expression_list)


def parse_ifs(tree):
    if tree.data == "if_only":
        condition = parse_expr(tree.children[0])
        contents = Group([create_statement_node(i) for i in tree.children[1:]])
        return If(condition, contents, None)

    elif tree.data == "if_else":
        if_node = parse_ifs(tree.children[0])
        if tree.children[1].data == "elif":
            _else = parse_ifs(tree.children[1].children[0].children[0])
        elif tree.children[1].data == "else":
            _else = Group([create_statement_node(i) for i in tree.children[1].children])
        else:
            raise ValueError("unknown node type")
        if_node._else = _else
        return if_node

    else:
        raise ValueError("unknown node type")


def create_statement_node(statement_node):
    rule_node = statement_node.children[0]
    if rule_node.data == "assignment":
        expr = parse_expr(rule_node.children[1])
        return Assignment(Variable(rule_node.children[0]), expr)

    elif rule_node.data == "if":
        return parse_ifs(rule_node.children[0])

    else:
        raise ValueError("unknown node type")


def parse(program: str):
    l = Lark(GRAMMAR, parser="lalr")
    tree = l.parse(program)

    statements = tree.children

    return Group([create_statement_node(i) for i in statements])


program = """

$xsdf = 11 $asdf1 111 $as1d111ff1;

if ($x 111){
    $asdf = 1;
    $fff = 11;
} else if (1 $a 11){
    $asdf = $fs;
} else {
    $apple = 1;
}

"""

parsed = parse(program)
print(parsed)
