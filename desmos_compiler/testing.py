from desmos_compiler.compiler import compile
from desmos_compiler.assembler import assemble

program = """
num counter = 4;

if (1 == 1){
    num counter = counter;
    counter = counter + 1;
    OUT = counter;
}

while (counter <= 3){
    counter = counter + 1;
}
OUT = counter;
"""

compile(program)

# compiled = compile(program)
# js = assemble(compiled)

# print(js)
