import ipaddress

import pytest

from subnet_calculator import allocate_vlsm, next_power_of_two


def test_next_power_of_two_rounds_up():
    assert next_power_of_two(1) == 2
    assert next_power_of_two(2) == 2
    assert next_power_of_two(3) == 4
    assert next_power_of_two(8) == 8
    assert next_power_of_two(9) == 16


def test_next_power_of_two_rejects_non_positive():
    with pytest.raises(ValueError):
        next_power_of_two(0)
    with pytest.raises(ValueError):
        next_power_of_two(-5)


def test_allocations_never_overlap_regardless_of_request_order():
    """Regression test for the original bug: requesting a small subnet
    before a larger one used to produce overlapping blocks, because the
    allocator advanced the cursor sequentially without accounting for the
    next block's alignment requirement."""
    base = ipaddress.IPv4Network("192.168.1.0/24")

    small_first = allocate_vlsm(base, [2, 8])
    large_first = allocate_vlsm(base, [8, 2])

    for allocations in (small_first, large_first):
        ranges = [
            (int(sub.network.network_address), int(sub.network.broadcast_address))
            for sub in allocations
        ]
        ranges.sort()
        for (start_a, end_a), (start_b, end_b) in zip(ranges, ranges[1:]):
            assert end_a < start_b, f"overlap: {ranges}"

    # Same requests, same base network -> same set of blocks, no matter what
    # order they were asked for in.
    small_first_blocks = sorted(str(sub.network) for sub in small_first)
    large_first_blocks = sorted(str(sub.network) for sub in large_first)
    assert small_first_blocks == large_first_blocks


def test_allocation_matches_request_order_in_output():
    base = ipaddress.IPv4Network("192.168.1.0/24")
    allocations = allocate_vlsm(base, [2, 8])
    assert allocations[0].requested_hosts == 2
    assert allocations[1].requested_hosts == 8
    assert allocations[0].network.prefixlen == 31  # 2 hosts -> /31
    assert allocations[1].network.prefixlen == 29  # 8 hosts -> /29


def test_allocation_fits_within_base_network():
    base = ipaddress.IPv4Network("10.0.0.0/30")  # only 4 addresses total
    allocations = allocate_vlsm(base, [2])
    assert allocations[0].network.subnet_of(base)


def test_allocation_raises_when_it_does_not_fit():
    base = ipaddress.IPv4Network("10.0.0.0/30")  # 4 addresses total
    with pytest.raises(ValueError):
        allocate_vlsm(base, [2, 4])  # needs 6, base only has 4


def test_slash_31_point_to_point_uses_both_addresses():
    base = ipaddress.IPv4Network("10.0.0.0/24")
    allocations = allocate_vlsm(base, [2])
    sub = allocations[0]
    assert sub.network.prefixlen == 31
    assert sub.usable_hosts == 2
    assert sub.first_usable == sub.network.network_address
    assert sub.last_usable == sub.network.broadcast_address
