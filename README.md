# desmos-compiler

Compile a C-like language to run in the [Desmos graphing calculator](https://www.desmos.com/calculator). The language currently supports variable definitions, scoping, if statements, while loops, and functions (with recursion).

The following steps are used to convert a program into a Desmos graph:
1. Parse the program and create an abstract syntax tree ([grammar specification](desmos_compiler/grammar.lark))
2. Compile the AST to "Desmos assembly", a set of low level instructions which can easily run in Desmos
3. Turn the generated Desmos assembly into expressions which can be pasted into Desmos

# Usage
Running `python -m desmos_compiler <path>` outputs a JavaScript command to stdout. Pasting this command into the console at [https://www.desmos.com/calculator](https://www.desmos.com/calculator) will use the Desmos API to create the expressions needed for the program to execute.

The first line in the Desmos graph will be an action called "Run", which runs the program as it is clicked. This can be sped up by clicking the "+" in the top left of the screen, selecting "ticker", typing "R_un" into the blank space, and pressing the play button. Once the program is done running, the result will be shown in the "Out" variable.

The "examples" directory contains example programs to help you get started.

# Setup
For normal usage, clone this repository and install the python package with `pip install -e .`

To run the tests, you will need to have Google Chrome installed. Download the `chromedriver` executable from [here](https://googlechromelabs.github.io/chrome-for-testing/#stable) and place it in the root directory of the repository. Make sure to get the `chromedriver` version that corresponds to your current version of Google Chrome.

# Testing
Run tests for this project using the `pytest` command after following the setup instructions.

# Features

- [x] Testing framework
- [x] Variables
- [x] Basic math
- [x] If/Else statements
- [x] While loops
- [x] Variable scoping / stack memory
- [x] Functions
- [x] Recursion
- [ ] Pointers
- [ ] Arrays
- [ ] Heap memory
- [ ] Structs
- [ ] Integration with graphs / visualizations
- [ ] Optimization
- [ ] Continuous integration testing on Github
