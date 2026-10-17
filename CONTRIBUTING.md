# Contributing

Thanks for considering a contribution to this project.

## Setup

```bash
git clone https://github.com/Mo-Sa-2004/ipv4-vlsm-calculator.git
cd ipv4-vlsm-calculator
pip install -r requirements-dev.txt
```

## Before opening a pull request

```bash
ruff check .                                                # lint
mypy subnet_calculator.py                                   # type checking
pytest --cov=subnet_calculator --cov-report=term-missing \
       --cov-fail-under=100                                 # tests + coverage
```

All three should pass clean — the same checks (plus executing the demo
notebook) run automatically in CI on every pull request.

## Guidelines

- Keep `allocate_vlsm` allocation-only; CLI input handling belongs in the
  `_prompt_*` / CLI functions, not mixed into the allocation logic.
- Add a test for any bug fix or new behavior — in particular, anything
  touching subnet alignment should include a case that would have caught
  the original overlap bug (see `test_subnet_calculator.py`).
- New test files need to be added to `testpaths` in `pyproject.toml`,
  which is an explicit whitelist rather than auto-discovery.
- Keep the README's example output in sync with the actual CLI output if
  you change the table format or prompts.
- The test suite is at 100% coverage, enforced in CI (`--cov-fail-under=100`).
  New code needs a test that covers it, not a lowered threshold.
