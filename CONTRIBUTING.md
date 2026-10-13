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
ruff check .      # lint
pytest             # tests
```

Both should pass clean — the same checks run automatically in CI on every
pull request.

## Guidelines

- Keep `allocate_vlsm` allocation-only; CLI input handling belongs in the
  `_prompt_*` / CLI functions, not mixed into the allocation logic.
- Add a test for any bug fix or new behavior — in particular, anything
  touching subnet alignment should include a case that would have caught
  the original overlap bug (see `test_subnet_calculator.py`).
- Keep the README's example output in sync with the actual CLI output if
  you change the table format or prompts.
