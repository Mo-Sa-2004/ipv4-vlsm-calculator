"""Tests for the output-rendering functions (_render_json, _render_table).

Neither of these had any direct test coverage before -- the only coverage
they got was incidentally, through test_cli.py's subprocess-based tests,
which coverage.py can't see since they run in a separate process.
"""

import ipaddress
import json

import subnet_calculator
from subnet_calculator import Subnet, _render_json, _render_table, allocate_vlsm

BASE = ipaddress.IPv4Network("192.168.1.0/24")


def test_render_json_is_valid_json_in_request_order():
    allocations = allocate_vlsm(BASE, [50, 20, 10, 2])
    result = json.loads(_render_json(allocations))

    assert [entry["requested_hosts"] for entry in result] == [50, 20, 10, 2]


def test_render_json_fields_match_the_allocated_subnet():
    sub = Subnet(network=ipaddress.IPv4Network("192.168.1.0/26"), requested_hosts=50)
    (entry,) = json.loads(_render_json([sub]))

    assert entry == {
        "network": "192.168.1.0/26",
        "start": "192.168.1.1",
        "end": "192.168.1.62",
        "hosts": 62,
        "broadcast": "192.168.1.63",
        "subnet_mask": "255.255.255.192",
        "prefix": 26,
        "requested_hosts": 50,
    }


def test_render_json_of_empty_list_is_empty_array():
    assert json.loads(_render_json([])) == []


def test_render_table_with_pandas_and_tabulate_produces_a_grid():
    allocations = allocate_vlsm(BASE, [50, 20])
    output = _render_table(allocations)

    # The grid table's header row and borders, plus every allocated network.
    assert "Network" in output
    assert "Hosts" in output
    assert "+---" in output
    for sub in allocations:
        assert str(sub.network.network_address) in output


def test_render_table_without_pandas_or_tabulate_falls_back_to_plain_text(monkeypatch):
    """_render_table checks `pd is None or tabulate is None` to decide
    whether to fall back -- simulate the deps being missing by patching
    those module-level names directly, the same way the real ImportError
    branch would leave them."""
    monkeypatch.setattr(subnet_calculator, "pd", None)
    monkeypatch.setattr(subnet_calculator, "tabulate", None)

    allocations = allocate_vlsm(BASE, [50, 20])
    output = _render_table(allocations)

    assert "pandas" in output
    assert "tabulate" in output
    assert "pip install -r requirements.txt" in output
    for i, sub in enumerate(allocations, start=1):
        assert f"{i}. {sub.network}" in output
        assert f"hosts={sub.usable_hosts}" in output
        assert f"range={sub.first_usable}-{sub.last_usable}" in output


def test_render_table_fallback_with_empty_list_has_no_entry_lines(monkeypatch):
    monkeypatch.setattr(subnet_calculator, "pd", None)
    monkeypatch.setattr(subnet_calculator, "tabulate", None)

    output = _render_table([])

    assert "pandas" in output
    assert output.strip().endswith("run `pip install -r requirements.txt` for a table):")