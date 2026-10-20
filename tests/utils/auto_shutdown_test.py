"""Tests for lottery_app.utils.auto_shutdown."""

import pytest

from lottery_app.utils import auto_shutdown


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Give each test a clean set of tabs and a controllable clock."""
    monkeypatch.setattr(auto_shutdown, "_tabs", {})
    monkeypatch.setattr(auto_shutdown, "_last_activity", None)
    clock = {"now": 1000.0}
    monkeypatch.setattr(auto_shutdown.time, "monotonic", lambda: clock["now"])
    return clock


def test_no_shutdown_before_any_browser_connects(reset_state):
    """The app keeps running if no browser has ever connected."""
    reset_state["now"] += 10_000
    assert not auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access


def test_open_tab_keeps_app_running(reset_state):
    """A tab that keeps pinging keeps the app alive."""
    auto_shutdown.record_heartbeat("tab1")
    reset_state["now"] += auto_shutdown.STALE_TAB_SECONDS - 1
    assert not auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access


def test_navigation_within_grace_period_keeps_app_running(reset_state):
    """Leaving one page and loading the next does not shut the app down."""
    auto_shutdown.record_heartbeat("tab1")
    auto_shutdown.record_tab_closed("tab1")
    reset_state["now"] += auto_shutdown.NAVIGATION_GRACE_SECONDS - 1
    assert not auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access
    auto_shutdown.record_heartbeat("tab1")
    reset_state["now"] += auto_shutdown.NAVIGATION_GRACE_SECONDS + 1
    assert not auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access


def test_shutdown_after_last_tab_closes(reset_state):
    """Once the last tab closes and the grace period passes, the app shuts down."""
    auto_shutdown.record_heartbeat("tab1")
    auto_shutdown.record_heartbeat("tab2")
    auto_shutdown.record_tab_closed("tab1")
    reset_state["now"] += auto_shutdown.NAVIGATION_GRACE_SECONDS + 1
    assert not auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access
    auto_shutdown.record_tab_closed("tab2")
    reset_state["now"] += auto_shutdown.NAVIGATION_GRACE_SECONDS + 1
    assert auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access


def test_silent_tab_is_dropped(reset_state):
    """A tab that stops pinging without closing is eventually treated as gone."""
    auto_shutdown.record_heartbeat("tab1")
    reset_state["now"] += auto_shutdown.STALE_TAB_SECONDS + 1
    assert auto_shutdown._should_shut_down(reset_state["now"])  # pylint: disable=protected-access


def test_shut_down_soon_interrupts_main_thread(monkeypatch):
    """The Quit button stops the app by interrupting the main thread."""
    calls = []
    monkeypatch.setattr(auto_shutdown._thread, "interrupt_main", lambda: calls.append(1))  # pylint: disable=protected-access
    monkeypatch.setattr(auto_shutdown.time, "monotonic", __import__("time").monotonic)

    auto_shutdown.shut_down_soon()
    __import__("time").sleep(1)

    assert calls == [1]
