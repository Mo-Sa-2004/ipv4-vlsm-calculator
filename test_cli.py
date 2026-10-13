"""End-to-end tests for the non-interactive CLI mode, run as a real
subprocess so they also exercise argument parsing and process exit codes."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "subnet_calculator.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_json_output_is_valid_and_non_overlapping():
    result = run("--network", "192.168.1.0/24", "--sizes", "50,20,10,2", "--json")
    assert result.returncode == 0

    subnets = json.loads(result.stdout)
    assert [s["requested_hosts"] for s in subnets] == [50, 20, 10, 2]

    ranges = sorted((s["network"], s["start"], s["end"]) for s in subnets)
    assert len(ranges) == len(subnets)  # all distinct networks, i.e. no dupes


def test_table_output_runs_without_error():
    result = run("--network", "192.168.1.0/24", "--sizes", "50,20,10,2")
    assert result.returncode == 0
    assert "192.168.1.0" in result.stdout


def test_invalid_network_exits_nonzero():
    result = run("--network", "not-a-network", "--sizes", "10")
    assert result.returncode != 0
    assert "Invalid --network" in result.stderr


def test_missing_sizes_exits_nonzero():
    result = run("--network", "192.168.1.0/24")
    assert result.returncode != 0
    assert "--sizes is required" in result.stderr


def test_request_too_large_exits_nonzero():
    result = run("--network", "10.0.0.0/30", "--sizes", "2,4")
    assert result.returncode != 0
    assert "Error" in result.stderr
