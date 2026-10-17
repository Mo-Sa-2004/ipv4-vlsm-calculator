# IPv4 VLSM Calculator

[![Tests](https://github.com/Mo-Sa-2004/ipv4-vlsm-calculator/actions/workflows/tests.yml/badge.svg)](https://github.com/Mo-Sa-2004/ipv4-vlsm-calculator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

A command-line tool that takes an IPv4 network and a list of subnet host
requirements, and allocates each one using **VLSM** (Variable Length Subnet
Masking) — giving every subnet the smallest block that fits its requirement,
with no gaps or overlaps.

## Features

- Splits any base network (e.g. `192.168.1.0/24`) into right-sized subnets
  from a list of "I need at least N hosts" requests.
- Requests can be entered in **any order** — the allocator always packs
  largest-first internally, which is required for correct, non-overlapping
  VLSM allocation, then reports results back in the order you asked for them.
- Validates input as you go (bad IP/mask, non-numeric sizes, requests that
  don't fit) instead of crashing.
- Correctly handles `/31` point-to-point links (both addresses usable, per
  [RFC 3021](https://www.rfc-editor.org/rfc/rfc3021)).
- Covered by unit tests, importable as a module if you want the allocation
  logic in your own code.
- Non-interactive mode (`--network` / `--sizes` / `--json`) for scripting,
  alongside the interactive prompts.

## Why "largest first" matters

A subnet of size *N* (a power of two) can only start at an address that is
itself a multiple of *N*. If you allocate a small subnet first and a larger
one afterward, the larger one can fail to land on a valid boundary — which
silently produces **overlapping subnets** instead of an error. This
calculator always allocates internally from largest request to smallest to
guarantee every block aligns correctly, regardless of the order you type
your requests in.

## Installation

```bash
git clone https://github.com/Mo-Sa-2004/ipv4-vlsm-calculator.git
cd ipv4-vlsm-calculator
pip install -r requirements.txt
```

Requires Python 3.10+.

Alternatively, install it as a package (adds a `vlsm-calc` command):

```bash
pip install -e .
vlsm-calc --network 192.168.1.0/24 --sizes 50,20,10,2
```

## Usage

```bash
python subnet_calculator.py
```

You'll be prompted for a base network, then asked for subnet sizes one at a
time (press Enter or type `0` when you're done adding subnets).

**Example:**

```
Enter the network IP address (example: 192.168.1.0): 192.168.1.0
Enter the network subnet mask (example: 255.255.255.0 or 24): 24
Enter the minimum size of subnet 1 (max remaining = 256, or press Enter to stop): 50
Enter the minimum size of subnet 2 (max remaining = 192, or press Enter to stop): 20
Enter the minimum size of subnet 3 (max remaining = 160, or press Enter to stop): 10
Enter the minimum size of subnet 4 (max remaining = 144, or press Enter to stop): 2
Enter the minimum size of subnet 5 (max remaining = 142, or press Enter to stop):

+---------------+---------------+---------------+---------+---------------+-----------------+----------+
| Network       | Start         | End           |   Hosts | Broadcast     | Subnet Mask     | Prefix   |
+===============+===============+===============+=========+===============+=================+==========+
| 192.168.1.0   | 192.168.1.1   | 192.168.1.62  |      62 | 192.168.1.63  | 255.255.255.192 | /26      |
+---------------+---------------+---------------+---------+---------------+-----------------+----------+
| 192.168.1.64  | 192.168.1.65  | 192.168.1.94  |      30 | 192.168.1.95  | 255.255.255.224 | /27      |
+---------------+---------------+---------------+---------+---------------+-----------------+----------+
| 192.168.1.96  | 192.168.1.97  | 192.168.1.110 |      14 | 192.168.1.111 | 255.255.255.240 | /28      |
+---------------+---------------+---------------+---------+---------------+-----------------+----------+
| 192.168.1.112 | 192.168.1.112 | 192.168.1.113 |       2 | 192.168.1.113 | 255.255.255.254 | /31      |
+---------------+---------------+---------------+---------+---------------+-----------------+----------+
```

### Non-interactive / scripted use

Pass `--network` and `--sizes` to skip the prompts entirely — useful in
scripts or CI:

```bash
python subnet_calculator.py --network 192.168.1.0/24 --sizes 50,20,10,2
```

Add `--json` for machine-readable output:

```bash
python subnet_calculator.py --network 192.168.1.0/24 --sizes 50,20,10,2 --json
```

```json
[
  {
    "network": "192.168.1.0/26",
    "start": "192.168.1.1",
    "end": "192.168.1.62",
    "hosts": 62,
    "broadcast": "192.168.1.63",
    "subnet_mask": "255.255.255.192",
    "prefix": 26,
    "requested_hosts": 50
  }
]
```

An invalid network, missing `--sizes`, or a request that doesn't fit exits
with a non-zero status and an error on stderr, so it's safe to use in a
pipeline.

## Using it as a library

```python
import ipaddress
from subnet_calculator import allocate_vlsm

base = ipaddress.IPv4Network("192.168.1.0/24")
subnets = allocate_vlsm(base, [50, 20, 10, 2])

for sub in subnets:
    print(sub.network, sub.usable_hosts, sub.first_usable, sub.last_usable)
```
## Notebook

[`subnet_calculator.ipynb`](subnet_calculator.ipynb) has the same example as
above, worked through interactively with `allocate_vlsm` imported directly
and the result shown as a `pandas` DataFrame. It's executed in CI on every
push and pull request, so it can't silently go stale.

## Running the tests
## Running the tests

```bash
pip install -r requirements-dev.txt
pytest       # unit tests, CLI end-to-end tests, and the doctest example
ruff check . # lint
```

Both run automatically in GitHub Actions on every push and pull request.
See [CONTRIBUTING.md](CONTRIBUTING.md) if you'd like to submit one.

## License

[MIT](LICENSE) — see [CHANGELOG.md](CHANGELOG.md) for version history.
