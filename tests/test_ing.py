from desmos_compiler.generate_desmos import DesmosExpr, generate_js
from conftest import run_program

def test_ing(driver):
    js = generate_js([
        DesmosExpr(id="run", latex="R_{un} = a \\to a+1"),
        DesmosExpr(id="in", latex="I_{n} = 1"),
        DesmosExpr(id="out", latex="O_{ut} = \\left[1\\right]"),
        DesmosExpr(id="done", latex="D_{one} = a"),
        DesmosExpr(id="0", latex="a=-10"),
        DesmosExpr(id="1", latex="x")
    ])

    output, exit_code = run_program(driver=driver, desmos_js=js, input=None, output_type="list")

    print(output, type(output))
    print(exit_code, type(exit_code))

def test_ing2(driver):
    js = generate_js([
        DesmosExpr(id="run", latex="R_{un} = a \\to a+1"),
        DesmosExpr(id="in", latex="I_{n} = 1"),
        DesmosExpr(id="out", latex="O_{ut} = \\left[1, 2, 3\\right]"),
        DesmosExpr(id="done", latex="D_{one} = a"),
        DesmosExpr(id="0", latex="a=-10"),
        DesmosExpr(id="1", latex="x")
    ])

    output, exit_code = run_program(driver=driver, desmos_js=js, input=None, output_type="list")

    print(output, type(output))
    print(exit_code, type(exit_code))
