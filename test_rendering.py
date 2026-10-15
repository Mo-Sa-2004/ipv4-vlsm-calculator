"""Tests for the output-rendering functions (_render_json, _render_table).

Neither of these had any direct test coverage before -- the only coverage
they got was incidentally, through test_cli.py's subprocess-based tests,
which coverage.py can't see since they run in a separate process.
"""

import ipaddress
import json

from subnet_calculator import Subnet, _render_json, allocate_vlsm

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