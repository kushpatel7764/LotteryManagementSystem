"""
bluetooth_bridge.py — Lottery Scanner Bluetooth Bridge

Connects to the iPhone scanner app over BLE and types every barcode
into the focused window on this computer, exactly like a USB barcode scanner.

Works on Windows 10/11 and macOS.

Requirements:
    pip install bleak pynput

Windows notes:
  - Requires Windows 10 version 1703+ (any modern Windows 10/11 is fine)
  - No special permissions needed — just run the script normally
  - Your laptop's built-in Bluetooth works; no dongle required

macOS notes:
  - System Settings → Privacy & Security → Accessibility → add Terminal

Usage:
    python bluetooth_bridge.py
"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
from pynput.keyboard import Controller, Key

# Must match BluetoothManager.swift on the iPhone
SERVICE_UUID      = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
BARCODE_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
DEVICE_NAME       = "LotteryScanner"

RECONNECT_DELAY = 3   # seconds between reconnection attempts
SCAN_TIMEOUT    = 6   # seconds per BLE scan pass

keyboard = Controller()


def type_barcode(code: str) -> None:
    """Type the barcode followed by Enter — identical to a physical scanner press."""
    keyboard.type(code)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def on_barcode(sender, data: bytearray) -> None:
    try:
        code = data.decode("utf-8").strip()
    except UnicodeDecodeError:
        print("[WARN] Received undecodable data, skipping.")
        return

    if not code:
        return

    print(f"[SCAN] {code}")
    type_barcode(code)


async def find_scanner():
    """Scan until the LotteryScanner peripheral is visible.

    Tries service UUID filtering first (most reliable), then falls back to
    device name matching in case Windows hides service UUIDs before pairing.
    """
    attempt = 0
    while True:
        attempt += 1
        print(f"[BT] Scanning for {DEVICE_NAME}… (attempt {attempt})", end="\r", flush=True)

        # Primary: match by advertised service UUID
        device = await BleakScanner.find_device_by_filter(
            lambda d, adv: (
                SERVICE_UUID.lower() in [str(u).lower() for u in adv.service_uuids]
                or (d.name or "").lower() == DEVICE_NAME.lower()
            ),
            timeout=SCAN_TIMEOUT,
        )

        if device:
            print(f"\n[BT] Found: {device.name or 'unknown'} ({device.address})")
            return device

        # Give the iPhone a moment (screen may have just turned on)
        await asyncio.sleep(1)


async def run_session(device) -> None:
    """Connect, subscribe to barcode notifications, and hold until disconnected."""
    print(f"[BT] Connecting to {device.name or device.address}…")
    try:
        async with BleakClient(device) as client:
            if not client.is_connected:
                print("[BT] Could not connect.")
                return

            print("[BT] Connected! Lottery scanner is active.")
            print("     Open the Scan Tickets page and make sure the barcode field is focused.\n")

            await client.start_notify(BARCODE_CHAR_UUID, on_barcode)

            while client.is_connected:
                await asyncio.sleep(0.5)

            print("\n[BT] iPhone disconnected.")

    except BleakError as exc:
        print(f"\n[BT] Connection error: {exc}")


async def main() -> None:
    print("=" * 50)
    print("  Lottery Scanner — Bluetooth Bridge")
    print("=" * 50)
    print("Ctrl+C to quit.\n")

    while True:
        try:
            device = await find_scanner()
            await run_session(device)
        except KeyboardInterrupt:
            print("\n[BT] Stopped by user.")
            sys.exit(0)
        except Exception as exc:
            print(f"[BT] Unexpected error: {exc}")

        print(f"[BT] Reconnecting in {RECONNECT_DELAY}s…")
        await asyncio.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    # On Windows, asyncio needs ProactorEventLoop for BLE to work.
    # Python 3.8+ sets this automatically via asyncio.run(), but we
    # set it explicitly here to be safe on all Windows Python versions.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
