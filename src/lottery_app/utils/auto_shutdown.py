"""
Shuts the app down once every browser tab using it has been closed.

The packaged app has no terminal window, so closing the browser would
otherwise leave the server running in the background with no way to stop it.

Each open page sends a heartbeat every few seconds with an ID for its tab,
and tells the server when it is going away. Once no tabs are left, the server
waits a short grace period (so moving between pages or refreshing does not
count as closing) and then shuts down. If a tab disappears without saying
goodbye (browser crash, laptop lid closed), it is dropped after it has been
silent for STALE_TAB_SECONDS. The Quit button in the nav bar stops the app
straight away.

Shutdown interrupts the main thread the same way Ctrl+C would, so the server
exits normally and atexit handlers (database re-encryption) still run.
"""

import _thread
import logging
import threading
import time

logger = logging.getLogger(__name__)

# How often each page pings the server. Must be well under the timeouts below.
HEARTBEAT_INTERVAL_SECONDS = 15
# Time allowed between one page closing and the next one loading.
NAVIGATION_GRACE_SECONDS = 10
# Browsers slow timers in background tabs to about once a minute, so a tab
# is only treated as gone after missing pings for longer than that.
STALE_TAB_SECONDS = 150
CHECK_INTERVAL_SECONDS = 2

_lock = threading.Lock()
_tabs = {}
_last_activity = None


def record_heartbeat(tab_id=None):
    """Mark the given tab (or just the app, if no tab is given) as active."""
    global _last_activity  # pylint: disable=global-statement
    now = time.monotonic()
    with _lock:
        _last_activity = now
        if tab_id:
            _tabs[tab_id] = now


def record_tab_closed(tab_id):
    """Forget a tab that told the server it is closing or navigating away."""
    global _last_activity  # pylint: disable=global-statement
    with _lock:
        _tabs.pop(tab_id, None)
        _last_activity = time.monotonic()


def _should_shut_down(now):
    """Return True when no tab has been heard from recently."""
    with _lock:
        if _last_activity is None:
            # No browser has connected yet, so there is nothing to wait for.
            return False
        for tab_id, last_seen in list(_tabs.items()):
            if now - last_seen > STALE_TAB_SECONDS:
                del _tabs[tab_id]
        return not _tabs and now - _last_activity > NAVIGATION_GRACE_SECONDS


def _watch():
    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        if _should_shut_down(time.monotonic()):
            logger.warning("All browser tabs closed; shutting down.")
            _thread.interrupt_main()
            return


def shut_down_soon():
    """Stop the app shortly, leaving time for the current response to be sent."""
    logger.warning("Quit requested from the browser; shutting down.")
    timer = threading.Timer(0.5, _thread.interrupt_main)
    timer.daemon = True
    timer.start()


def start_watchdog():
    """Start the background thread that stops the app once all tabs close."""
    threading.Thread(target=_watch, daemon=True, name="auto-shutdown").start()
