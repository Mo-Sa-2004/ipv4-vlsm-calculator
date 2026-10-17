import ipaddress

import pytest

from subnet_calculator import Subnet, allocate_vlsm, next_power_of_two


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
        for (_start_a, end_a), (start_b, _end_b) in zip(
            ranges, ranges[1:], strict=False
        ):
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


def test_non_positive_request_error_names_which_request_number():
    """Regression test: this error used to just say 'subnet size must be a
    positive number' with no way to tell which of several requests caused
    it, unlike the 'doesn't fit' error above, which does."""
    base = ipaddress.IPv4Network("192.168.1.0/24")
    with pytest.raises(ValueError, match=r"Request #2: .*positive number"):
        allocate_vlsm(base, [10, 0, 5])

def test_slash_31_point_to_point_uses_both_addresses():
    base = ipaddress.IPv4Network("10.0.0.0/24")
    allocations = allocate_vlsm(base, [2])
    sub = allocations[0]
    assert sub.network.prefixlen == 31
    assert sub.usable_hosts == 2
    assert sub.first_usable == sub.network.network_address
    assert sub.last_usable == sub.network.broadcast_address


def test_slash_32_single_host_route():
    """allocate_vlsm never produces a /32 on its own (every request rounds
    up to at least 2 addresses), but Subnet's own properties should still
    be correct for one, since nothing stops a /32 from being constructed
    directly -- e.g. by code reusing Subnet outside allocate_vlsm."""
    sub = Subnet(
        network=ipaddress.IPv4Network("10.0.0.5/32"),
        requested_hosts=1,
    )
    assert sub.usable_hosts == 1
    assert sub.first_usable == sub.last_usable == ipaddress.IPv4Address("10.0.0.5")


def test_exact_fit_consumes_the_whole_base_network():
    """Requests that add up to exactly the base network's capacity should
    allocate cleanly, not raise, and use every address."""
    base = ipaddress.IPv4Network("10.0.0.0/29")  # 8 addresses total
    allocations = allocate_vlsm(base, [4, 2, 2])  # rounds to 4 + 2 + 2 = 8

    last = allocations[-1]
    assert sorted(a.network.network_address for a in allocations)[0] == base.network_address
    # the final allocated block's broadcast address should be the base
    # network's own broadcast address -- no address left unused, none spilled over
    highest_broadcast = max(int(a.network.broadcast_address) for a in allocations)
    assert highest_broadcast == int(base.broadcast_address)
    assert last.network.subnet_of(base)


def test_large_base_network_allocates_without_overlap():
    """Sanity check at a much bigger scale than the other tests (a /8
    instead of a /24-ish network) with a mix of very different sizes."""
    base = ipaddress.IPv4Network("10.0.0.0/8")
    requested = [2, 100000, 4, 500000, 1000, 2000000]

    allocations = allocate_vlsm(base, requested)

    assert [a.requested_hosts for a in allocations] == requested

    ranges = sorted(
        (int(a.network.network_address), int(a.network.broadcast_address))
        for a in allocations
    )
    for (_start_a, end_a), (start_b, _end_b) in zip(ranges, ranges[1:], strict=False):
        assert end_a < start_b, f"overlap at large scale: {ranges}"

    for a in allocations:
        assert a.network.subnet_of(base)
