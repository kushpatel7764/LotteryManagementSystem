// Lets the app know this tab is still open, so it can shut itself down once
// every tab has been closed. The tab ID lives in sessionStorage so it stays the
// same while moving between pages in one tab.
(function () {
  const INTERVAL_MS = 15000;

  let tabId = null;
  try {
    tabId = sessionStorage.getItem('appTabId');
    if (!tabId) {
      tabId = Date.now().toString(36) + Math.random().toString(36).slice(2);
      sessionStorage.setItem('appTabId', tabId);
    }
  } catch (e) {
    tabId = Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  function ping() {
    fetch('/heartbeat?tab=' + encodeURIComponent(tabId), { cache: 'no-store' }).catch(() => {});
  }

  ping();
  setInterval(ping, INTERVAL_MS);

  // Ping right away when a hidden tab comes back, in case the browser slowed
  // down its timers while it was in the background.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') ping();
  });
  window.addEventListener('pageshow', (e) => { if (e.persisted) ping(); });

  // Closing the tab and moving to another page look the same from here, so the
  // server waits a few seconds for the next page to ping before shutting down.
  window.addEventListener('pagehide', () => {
    navigator.sendBeacon('/heartbeat/closed?tab=' + encodeURIComponent(tabId));
  });
})();
