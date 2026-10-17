"""In-process tests for main()'s non-interactive (--network/--sizes) path.

test_cli.py already covers this end-to-end via real subprocesses, which is
valuable for genuine confidence that argument parsing and exit codes work
from an actual command line -- but coverage.py can't see into a separate
process, so none of it counted toward the coverage numbers. These call
main(argv) directly in-process instead, to close that gap. The subprocess
tests in test_cli.py stay as-is; this file doesn't replace them.
"""

import json

import pytest

from subnet_calculator import main


def test_table_output(capsys):
    main(["--network", "192.168.1.0/24", "--sizes", "50,20,10,2"])

    out = capsys.readouterr().out
    assert "192.168.1.0" in out
    assert "Network" in out


def test_json_output(capsys):
    main(["--network", "192.168.1.0/24", "--sizes", "50,20,10,2", "--json"])

    subnets = json.loads(capsys.readouterr().out)
    assert [s["requested_hosts"] for s in subnets] == [50, 20, 10, 2]


def test_invalid_network_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--network", "not-a-network", "--sizes", "10"])

    assert exc_info.value.code == 2
    assert "Invalid --network" in capsys.readouterr().err


def test_missing_sizes_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--network", "192.168.1.0/24"])

    assert exc_info.value.code == 2
    assert "--sizes is required" in capsys.readouterr().err


def test_invalid_sizes_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--network", "192.168.1.0/24", "--sizes", "50,not-a-number"])

    assert exc_info.value.code == 2
    assert "Invalid --sizes" in capsys.readouterr().err


def test_request_too_large_exits_with_code_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--network", "10.0.0.0/30", "--sizes", "2,4"])

    assert exc_info.value.code == 1
    assert "Error" in capsys.readouterr().err


def test_sizes_that_parse_to_nothing_prints_nothing_to_allocate(capsys):
    """--sizes "," is non-empty (so it passes the "is --sizes given at all"
    check) but splits into no actual numbers once blanks are filtered out."""
    main(["--network", "192.168.1.0/24", "--sizes", ","])

    out, err = capsys.readouterr()
    assert "No subnets requested" in out
    assert err == ""