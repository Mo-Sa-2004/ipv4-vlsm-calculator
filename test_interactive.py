"""Tests for the interactive-prompt path: _prompt_network, _prompt_sizes,
and main() with no --network/--sizes given.

None of this had any direct coverage before -- it only runs when the CLI
is invoked with no arguments, which test_cli.py never does (it always
passes --network/--sizes to stay non-interactive).
"""

import ipaddress

from subnet_calculator import _prompt_network, _prompt_sizes, main


def _feed(monkeypatch, *answers):
    """Make input() return `answers` in order, one per call."""
    responses = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))


def test_prompt_network_accepts_valid_ip_and_mask(monkeypatch):
    _feed(monkeypatch, "192.168.1.0", "24")
    assert _prompt_network() == ipaddress.IPv4Network("192.168.1.0/24")


def test_prompt_network_accepts_dotted_mask(monkeypatch):
    _feed(monkeypatch, "10.0.0.0", "255.255.255.0")
    assert _prompt_network() == ipaddress.IPv4Network("10.0.0.0/24")


def test_prompt_network_reprompts_after_invalid_input(monkeypatch, capsys):
    _feed(monkeypatch, "not-an-ip", "24", "192.168.1.0", "24")
    result = _prompt_network()

    assert result == ipaddress.IPv4Network("192.168.1.0/24")
    assert "not a valid network" in capsys.readouterr().out


def test_prompt_sizes_collects_until_enter_pressed(monkeypatch):
    _feed(monkeypatch, "50", "20", "")
    assert _prompt_sizes(max_size=256) == [50, 20]


def test_prompt_sizes_stops_on_explicit_zero(monkeypatch):
    _feed(monkeypatch, "50", "0")
    assert _prompt_sizes(max_size=256) == [50]


def test_prompt_sizes_reprompts_on_non_numeric_input(monkeypatch, capsys):
    _feed(monkeypatch, "not-a-number", "10", "")
    result = _prompt_sizes(max_size=256)

    assert result == [10]
    assert "whole number" in capsys.readouterr().out


def test_prompt_sizes_reprompts_on_non_positive_size(monkeypatch, capsys):
    _feed(monkeypatch, "-5", "10", "")
    result = _prompt_sizes(max_size=256)

    assert result == [10]
    assert "positive number" in capsys.readouterr().out


def test_prompt_sizes_stops_without_reprompting_when_request_does_not_fit(
    monkeypatch, capsys
):
    """Unlike the other invalid-input cases, a request that doesn't fit in
    what's left breaks out of the loop (keeping what was already collected)
    instead of asking again."""
    _feed(monkeypatch, "2", "100")
    result = _prompt_sizes(max_size=4)

    assert result == [2]
    assert "only" in capsys.readouterr().out


def test_main_interactive_path_runs_end_to_end(monkeypatch, capsys):
    _feed(monkeypatch, "192.168.1.0", "24", "50", "20", "")
    main([])

    out = capsys.readouterr().out
    assert "192.168.1.0" in out
    assert "Network" in out  # table header


def test_main_interactive_path_with_no_subnets_requested(monkeypatch, capsys):
    _feed(monkeypatch, "192.168.1.0", "24", "")
    main([])

    assert "No subnets requested" in capsys.readouterr().out