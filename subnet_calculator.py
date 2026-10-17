"""VLSM (Variable Length Subnet Mask) calculator.

Given a base network and a list of required subnet sizes (minimum number of
usable hosts), this allocates one subnet per request out of the base network
without overlaps, and prints the result as a table.

Run it directly for the interactive CLI:

    python subnet_calculator.py

Or import `allocate_vlsm` to use the logic from your own code.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from dataclasses import dataclass
from typing import Any

__version__ = "0.2.0"

pd: Any
tabulate: Any

try:
    import pandas as pd
    import tabulate
except ImportError:  # pragma: no cover - exercised only when deps are missing
    pd = None
    tabulate = None


def next_power_of_two(n: int) -> int:
    """Round `n` up to the next power of two.

    Every subnet needs at least 2 addresses (network + broadcast), so the
    result is never smaller than 2.
    """
    if n < 1:
        raise ValueError("subnet size must be a positive number")
    power = 2
    while power < n:
        power *= 2
    return power


@dataclass
class Subnet:
    """One allocated subnet, plus the host count that was originally asked for."""

    network: ipaddress.IPv4Network
    requested_hosts: int

    @property
    def usable_hosts(self) -> int:
        if self.network.prefixlen >= 31:
            # RFC 3021: /31 point-to-point links use both addresses (no
            # network/broadcast reserved); /32 is a single host route.
            return self.network.num_addresses
        return self.network.num_addresses - 2

    @property
    def first_usable(self) -> ipaddress.IPv4Address:
        if self.network.prefixlen >= 31:
            return self.network.network_address
        return self.network.network_address + 1

    @property
    def last_usable(self) -> ipaddress.IPv4Address:
        if self.network.prefixlen >= 31:
            return self.network.broadcast_address
        return self.network.broadcast_address - 1


def allocate_vlsm(
    base: ipaddress.IPv4Network, requested_sizes: list[int]
) -> list[Subnet]:
    """Allocate one subnet per entry in `requested_sizes` out of `base`.

    Requests are satisfied largest-first, regardless of the order they were
    given in, and the result is returned back in the original request order.

    This ordering is required, not a style choice: a block of size N (a
    power of two) can only start at an address that is itself a multiple of
    N. Allocating in descending order of size guarantees every block lands
    on a valid boundary; allocating smaller blocks before larger ones can
    make a later, larger block fail to align, which silently produces
    overlapping subnets instead of a clean partition.

    Raises ValueError if a requested size can't fit in what's left of `base`.

    >>> import ipaddress
    >>> base = ipaddress.IPv4Network("192.168.1.0/24")
    >>> for sub in allocate_vlsm(base, [2, 8]):
    ...     print(sub.network, sub.usable_hosts)
    192.168.1.8/31 2
    192.168.1.0/29 6
    """
    order = sorted(range(len(requested_sizes)), key=lambda i: -requested_sizes[i])

    allocations: list[Subnet | None] = [None] * len(requested_sizes)
    cursor = int(base.network_address)
    limit = int(base.broadcast_address) + 1

        for i in order:
        try:
            size = next_power_of_two(requested_sizes[i])
        except ValueError as exc:
            raise ValueError(f"Request #{i + 1}: {exc}") from exc
        if cursor + size > limit:
            raise ValueError(
                f"Request #{i + 1} needs {requested_sizes[i]} addresses "
                f"(rounded up to {size}), but only {limit - cursor} remain "
                f"in {base}."
            )

        prefix = 32 - (size.bit_length() - 1)
        network = ipaddress.IPv4Network((cursor, prefix))
        allocations[i] = Subnet(network=network, requested_hosts=requested_sizes[i])
        cursor += size

    return allocations  # type: ignore[return-value]


def _prompt_network() -> ipaddress.IPv4Network:
    while True:
        ip = input("Enter the network IP address (example: 192.168.1.0): ").strip()
        mask = input(
            "Enter the network subnet mask (example: 255.255.255.0 or 24): "
        ).strip()
        try:
            return ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
        except ValueError as exc:
            print(f"That's not a valid network ({exc}). Try again.\n")


def _prompt_sizes(max_size: int) -> list[int]:
    sizes: list[int] = []
    used = 0
    counter = 1

    while used < max_size:
        remaining = max_size - used
        raw = input(
            f"Enter the minimum size of subnet {counter} "
            f"(max remaining = {remaining}, or press Enter to stop): "
        ).strip()

        if not raw or raw == "0":
            break

        try:
            size = int(raw)
        except ValueError:
            print("Please enter a whole number.\n")
            continue

        if size < 1:
            print("Subnet size must be a positive number.\n")
            continue

        rounded = next_power_of_two(size)
        if used + rounded > max_size:
            print(
                f"That needs {rounded} addresses once rounded up to a power "
                f"of two, but only {remaining} are left. Try a smaller size."
            )
            break

        sizes.append(size)
        used += rounded
        counter += 1

    return sizes


def _render_json(allocations: list[Subnet]) -> str:
    return json.dumps(
        [
            {
                "network": str(sub.network),
                "start": str(sub.first_usable),
                "end": str(sub.last_usable),
                "hosts": sub.usable_hosts,
                "broadcast": str(sub.network.broadcast_address),
                "subnet_mask": str(sub.network.netmask),
                "prefix": sub.network.prefixlen,
                "requested_hosts": sub.requested_hosts,
            }
            for sub in allocations
        ],
        indent=2,
    )


def _render_table(allocations: list[Subnet]) -> str:
    if pd is None or tabulate is None:
        lines = [
            "'pandas' and 'tabulate' aren't installed, so here's the plain "
            "result (run `pip install -r requirements.txt` for a table):",
            "",
        ]
        lines += [
            f"{i}. {sub.network}  hosts={sub.usable_hosts}  "
            f"range={sub.first_usable}-{sub.last_usable}"
            for i, sub in enumerate(allocations, start=1)
        ]
        return "\n".join(lines)

    df = pd.DataFrame(
        [
            [
                str(sub.network.network_address),
                str(sub.first_usable),
                str(sub.last_usable),
                sub.usable_hosts,
                str(sub.network.broadcast_address),
                str(sub.network.netmask),
                f"/{sub.network.prefixlen}",
            ]
            for sub in allocations
        ],
        columns=["Network", "Start", "End", "Hosts", "Broadcast", "Subnet Mask", "Prefix"],
    )
    return tabulate.tabulate(
        df.values.tolist(), headers=list(df.columns), tablefmt="grid"
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "VLSM calculator. Run with no arguments for the interactive "
            "prompts, or pass --network and --sizes to run non-interactively "
            "(handy for scripts)."
        )
    )
    parser.add_argument(
        "--network",
        help="Base network, e.g. 192.168.1.0/24 (enables non-interactive mode).",
    )
    parser.add_argument(
        "--sizes",
        help="Comma-separated minimum host counts, e.g. 50,20,10,2 "
        "(required when --network is given).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of a table.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.network:
        try:
            network = ipaddress.IPv4Network(args.network, strict=False)
        except ValueError as exc:
            print(f"Invalid --network: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc

        if not args.sizes:
            print("--sizes is required when --network is given.", file=sys.stderr)
            raise SystemExit(2)

        try:
            sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
        except ValueError as exc:
            print(f"Invalid --sizes: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
    else:
        network = _prompt_network()
        sizes = _prompt_sizes(network.num_addresses)

    if not sizes:
        print("No subnets requested — nothing to allocate.")
        return

    try:
        allocations = allocate_vlsm(network, sizes)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    output = _render_json(allocations) if args.json else _render_table(allocations)
    print(("\n" + output) if not args.json else output)


if __name__ == "__main__":  # pragma: no cover - trivial script entry point
    main()