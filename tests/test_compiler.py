import pytest
from desmos_compiler.compiler import compile_syntax_tree
from tests.utils import run_program_js
from desmos_compiler.parser import parse
from desmos_compiler.assembler import assemble


@pytest.fixture
def prog_tester(driver):
    def _ret(prog, input, expected_output):
        syntax_tree = parse(prog)
        desmos_assembly = compile_syntax_tree(syntax_tree)
        js = assemble(desmos_assembly)
        program_output = run_program_js(
            driver=driver, desmos_js=js, program_input=str(input)
        )
        assert program_output.exit_code == 0
        assert program_output.output == expected_output

    return _ret


@pytest.mark.parametrize("input,expected_output", [(5, 2), (7, 7)])
def test_math(prog_tester, input, expected_output):
    prog_tester("OUT = 1 + 2*3 % IN;", input, expected_output)


@pytest.mark.parametrize("input,expected_output", [(0, 4), (3, 10)])
def test_variables(prog_tester, input, expected_output):
    prog_tester(
        """
        num x;
        num y;
        x = IN;
        x = x + 2;
        y = 2*x;
        OUT = y;
        """,
        input,
        expected_output,
    )


@pytest.mark.parametrize("input,expected_output", [(0, 2), (5, 4), (8, 35)])
def test_if(prog_tester, input, expected_output):
    prog_tester(
        """
        num x;
        x = 5;
        if (IN < 5){
            x = 1;
        }
        if (IN < 6){
            x = 2;
        }

        num y;
        if (IN < 5){
            y = 1;
        } else if (IN < 6){
            y = 2;
        } else {
            y = 7;
        }

        OUT = x * y;
        """,
        input,
        expected_output,
    )


def test_if_scope(prog_tester):
    prog_tester(
        """
        OUT = 0;

        num x;
        x = 0;
        if (x == 0){
            OUT = OUT + 1;

            num x;
            x = 2;
            if (x == 2){
                OUT = OUT + 1;
            }
        }

        if (x == 0){
            OUT = OUT + 1;
        }

        """,
        0,
        3,
    )


@pytest.mark.parametrize("input,expected_output", [(2, 32), (3, 48)])
def test_while(prog_tester, input, expected_output):
    prog_tester(
        """
        while (IN < 32){
            IN = IN * 2;
        }
        OUT = IN;
        """,
        input,
        expected_output,
    )


@pytest.mark.parametrize("input,expected_output", [(3, 50), (14, 54), (35, 110)])
def test_simple_func(prog_tester, input, expected_output):
    prog_tester(
        """
        num max(num x, num y){
            if (x >= y){
                return x;
            } else {
                return y;
            }
        }
        OUT = max(10, IN) + max(15, IN) + max(20, IN);
        OUT = OUT + max(1, max(max(4, max(1, 5)), 2));
        """,
        input,
        expected_output,
    )


@pytest.mark.parametrize(
    "input,expected_output", [(3, 3), (2, 1), (18, 3), (20, 5), (23, 1)]
)
def test_recursion_gcd(prog_tester, input, expected_output):
    prog_tester(
        """
        num gcd(num a, num b){
            if (b == 0){
                return a;
            }
            return gcd(b, a % b);
        }
        OUT = gcd(15, IN);
        """,
        input,
        expected_output,
    )


@pytest.mark.parametrize("input,expected_output", [(0, 0), (1, 1), (8, 21)])
def test_recursion_fib(prog_tester, input, expected_output):
    prog_tester(
        """
        num fib(num a, num b, num counter){
            if (counter == 0){
                return a;
            }
            return fib(b, a+b, counter - 1);
        }
        OUT = fib(0, 1, IN);
        """,
        input,
        expected_output,
    )


@pytest.mark.parametrize("input,expected_output", [(0, 1), (1, 0), (3, 0), (6, 1)])
def test_mutual_recursion(prog_tester, input, expected_output):
    prog_tester(
        """
        num even(num x){
            if (x == 0){
                return 1;
            }
            return odd(x - 1);
        }

        num odd(num x){
            if (x == 0){
                return 0;
            }
            return even(x - 1);
        }
        OUT = even(IN);
        """,
        input,
        expected_output,
    )
