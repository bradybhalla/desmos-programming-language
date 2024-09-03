import sys
from desmos_compiler.compiler import compile_syntax_tree
from desmos_compiler.assembler import assemble
from desmos_compiler.parser import parse

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        program = f.read()

    ast = parse(program)
    desmos_assembly = compile_syntax_tree(ast)
    js = assemble(desmos_assembly)

    print(js)
