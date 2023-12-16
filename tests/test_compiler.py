import pytest
from conftest import run_program_js
from desmos_compiler.assembler import assemble
from desmos_compiler.compiler import compile

# a slightly overcomplicated Fibonacci sequence calculator
FIB_PROGRAM = """
$counter = $IN;

if ($counter <= 1) {
    $OUT = $counter;
}
else {
    $prev = 0;
    $curr = 1;
    $i = 2;

    while ($i != $counter + 1) {
        $temp = $prev + ($curr - 2)*3 + 13%7 - 4*$curr / 2;
        $prev = $curr;
        $curr = $temp;
        $i = $i + 1;
    }

    $OUT = $curr;
}
$DONE = 0;
"""


def fib_expected(x):
    i = 1
    j = 0
    for _ in range(x):
        i, j = j, i + j
    return j


@pytest.mark.parametrize("program_inputs", [[0, 10, 15]])
@pytest.mark.parametrize(
    "program",
    [
        (FIB_PROGRAM, fib_expected),
    ],
)
def test_compile(driver, program, program_inputs):
    prog, expected = program
    asm = compile(prog)
    js = assemble(asm)

    for i in program_inputs:
        output, exit_code = run_program_js(driver=driver, desmos_js=js, program_input=i)
        assert exit_code == 0
        assert output == expected(i)
