from desmos_compiler.compiler import compile_syntax_tree
from desmos_compiler.assembler import assemble
from desmos_compiler.parser import parse

program = """
num max(num x, num y){
    if (x >= y){
        return x;
    } else {
        return y;
    }
}

OUT = max(10, IN);
"""

syntax_tree = parse(program)
desmos_assembly = compile_syntax_tree(syntax_tree)
js = assemble(desmos_assembly)

# print(desmos_assembly)
print(js)
