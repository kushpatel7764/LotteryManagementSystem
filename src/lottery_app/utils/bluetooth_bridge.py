"""
Bluetooth bridge — runs inside the Flask app as a daemon thread.
Discovers the LotteryScanner iPhone app over BLE and types each barcode
as keystrokes into the focused window, exactly like a USB barcode scanner.
"""
import asyncio
import logging
import sys
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_SERVICE_UUID      = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
_BARCODE_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
_DEVICE_NAME       = "LotteryScanner"
_SCAN_TIMEOUT      = 6
_RECONNECT_DELAY   = 3


class BluetoothBridge:
    """Manages the BLE → keystroke pipeline in a background daemon thread."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._loop:   Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        self.status = "off"  # "off" | "scanning" | "connected"

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.is_running:
            return
        self._stop_event.clear()
        self.status = "scanning"
        self._thread = threading.Thread(
            target=self._thread_main, daemon=True, name="bt-bridge"
        )
        self._thread.start()
        logger.info("Bluetooth bridge started.")

    def stop(self):
        self._stop_event.set()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.status = "off"
        logger.info("Bluetooth bridge stopped.")

    def _thread_main(self):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_main())
        except Exception as exc:
            logger.error("Bluetooth bridge crashed: %s", exc)
        finally:
            loop.close()
            self._loop = None
            self.status = "off"

    async def _async_main(self):
        from bleak import BleakScanner, BleakClient
        from bleak.exc import BleakError
        from pynput.keyboard import Controller, Key

        keyboard = Controller()

        def on_barcode(_sender, data: bytearray):
            try:
                code = data.decode("utf-8").strip()
                if code:
                    logger.info("[BT] Barcode: %s", code)
                    keyboard.type(code)
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)
            except Exception as exc:
                logger.warning("[BT] Decode error: %s", exc)

        while not self._stop_event.is_set():
            try:
                self.status = "scanning"
                device = None

                while not self._stop_event.is_set() and device is None:
                    device = await BleakScanner.find_device_by_filter(
                        lambda d, adv: (
                            _SERVICE_UUID.lower() in [str(u).lower() for u in adv.service_uuids]
                            or (d.name or "").lower() == _DEVICE_NAME.lower()
                        ),
                        timeout=_SCAN_TIMEOUT,
                    )

                if self._stop_event.is_set() or device is None:
                    break

                logger.info("[BT] Connecting to %s …", device.name or device.address)
                self.status = "connected"

                async with BleakClient(device) as client:
                    if client.is_connected:
                        await client.start_notify(_BARCODE_CHAR_UUID, on_barcode)
                        while client.is_connected and not self._stop_event.is_set():
                            await asyncio.sleep(0.5)

                if not self._stop_event.is_set():
                    self.status = "scanning"
                    await asyncio.sleep(_RECONNECT_DELAY)

            except (BleakError, Exception) as exc:
                logger.error("[BT] Session error: %s", exc)
                if not self._stop_event.is_set():
                    await asyncio.sleep(_RECONNECT_DELAY)

        self.status = "off"


# Module-level singleton — one instance shared across the entire app
bluetooth_bridge = BluetoothBridge()
