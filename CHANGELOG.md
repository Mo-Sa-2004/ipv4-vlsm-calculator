# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Fixed

- **VLSM allocation overlap bug.** `allocate_vlsm` previously assigned
  subnets in the order they were requested, advancing a cursor sequentially
  with no regard for each block's alignment requirement. A block of size N
  (a power of two) can only start at an address that is itself a multiple
  of N — so requesting a small subnet before a larger one could leave the
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
