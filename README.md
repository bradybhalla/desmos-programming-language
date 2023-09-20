# desmos-compiler

Compile a simple programming language to run in [Desmos graphing calculator](https://www.desmos.com/calculator).

## Setup

1. Clone the repository
2. `pip install -e ".[dev]"`
3. Ensure that Google Chrome is installed
4. Download `chromedriver` and place the executable in the root directory of the repo. Download from [here](https://googlechromelabs.github.io/chrome-for-testing/#stable).

## Usage

```bash
cd tests/
pytest
```

For now, running the tests are the best way to see this project in action.
