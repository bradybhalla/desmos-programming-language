# Standard for Generated Desmos Expressions

## Required expressions
| id   | variable name | description                              |  type
|------|---------------|------------------------------------------|----------------
| run  | `R_{un}`      | Action which is run until `D_{one} >= 0` |  action
| in   | `I_{n}`       | Input                                    |  number or list
| out  | `O_{ut}`      | Output                                   |  number or list
| done | `D_{one}`     | Initialized `< 0`, exit when `>= 0`      |  integer

## Exit codes
- The exit code is the value of `D_{one}` once it is `>= 0`
- An exit code of `0` means there is no error
