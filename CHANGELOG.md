# Changelog

All notable changes to this project are documented here.

## [0.3.0]

### Added

- mypy type checking, run in CI alongside ruff.
- Test coverage reporting (`pytest-cov`), with CI enforcing 100% -- closed
  real gaps that had zero coverage: `_render_json`, `_render_table` (both
  the pandas/tabulate path and the plain-text fallback used when those
  deps are missing), the entire interactive prompt path
  (`_prompt_network`, `_prompt_sizes`, interactive `main()`), and the
  `--network`/`--sizes` CLI error branches.
- The demo notebook (`subnet_calculator.ipynb`) is now linked from the
  README and executed in CI on every push/PR, so it can't go stale
  silently.
- `pyproject.toml` packaging metadata: classifiers, `project.urls`,
  keywords, and an SPDX `license` expression.

### Fixed

- Two real mypy issues in `subnet_calculator.py`: the `pandas`/`tabulate`
  optional-import fallback wasn't typed correctly, and `tabulate.tabulate()`
  was being called in a way its stubs don't model for pandas DataFrames
  (worked at runtime, but failed type checking). Output is unchanged.
- CI now actually runs `ruff check .` -- the README and CONTRIBUTING docs
  had claimed it did since 0.2.0, but the workflow only ever ran `pytest`.
- `allocate_vlsm`'s error for a non-positive requested size (0 or
  negative) didn't say which request caused it, unlike the "doesn't fit"
  error, which does. Both are consistent now.
- `.gitignore` didn't cover `.mypy_cache/` or coverage artifacts
  (`.coverage`, `htmlcov/`) -- found one sitting untracked in a clean
  clone.

## [0.2.0]

### Added

- Non-interactive CLI mode: `--network`, `--sizes`, and `--json`, for
  scripting and automation use instead of the interactive prompts.
- `--version` flag.
- Package metadata (`pyproject.toml`) -- the project is now pip-installable
  and exposes a `vlsm-calc` console command.
- Ruff linting, CI (GitHub Actions) running the test suite on every push,
  a doctest usage example, and more edge-case tests (`/32`, exact-fit
  allocation, large `/8` networks).

## [0.1.0]

### Fixed

- **VLSM allocation overlap bug.** `allocate_vlsm` previously assigned
  subnets in the order they were requested, advancing a cursor sequentially
  with no regard for each block's alignment requirement. A block of size N
  (a power of two) can only start at an address that is itself a multiple
  of N -- so requesting a small subnet before a larger one could leave the
  larger one unable to align, and the two would silently overlap instead of
  erroring. Example: on `192.168.1.0/24`, requesting a 2-host subnet
  followed by an 8-host subnet previously placed both at `192.168.1.0`.
  Subnets are now always allocated largest-first internally (then reported
  back in the order requested), which guarantees correct alignment
  regardless of input order. Covered by a regression test.
- Invalid input (a malformed IP/mask, a non-numeric subnet size, a request
  that doesn't fit in the remaining space) now prints a clear message and
  re-prompts instead of crashing with a traceback.

### Added

- Unit test suite (`test_subnet_calculator.py`).
- `README.md`, `LICENSE` (MIT), `requirements.txt` / `requirements-dev.txt`.
- Allocation logic split out into an importable `allocate_vlsm` function,
  separate from the interactive CLI prompting.