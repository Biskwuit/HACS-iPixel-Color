"""Data coordinator for iPixel Color devices."""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

import pypixelcolor
from homeassistant.core import HomeAssistant

from .const import (
    ADAPTER,
    DEFAULT_ANIMATION,
    DEFAULT_BRIGHTNESS,
    DEFAULT_COLOR,
    DEFAULT_RESIZE_METHOD,
    DEFAULT_SPEED,
    SCAN_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


def _scan_for_devices() -> list[dict]:
    """Scan for nearby iPixel Color BLE devices and return address/name list."""
    try:
        import bleak

        async def _async_scan():
            discovered: dict[str, str] = {}
            scanner = bleak.BleakScanner(adapter=ADAPTER)

            def _on_discovery(device, advertisement_data):
                name = device.name or advertisement_data.local_name or ""
                if not name:
                    return
                addr = device.address
                # Filter by known iPixel Color advertisement prefixes
                if any(
                    prefix in name.upper()
                    for prefix in ("IPIXEL", "PIXEL", "MATRIX", "COLOR")
                ):
                    discovered[addr] = name

            scanner.register_detection_callback(_on_discovery)
            await scanner.start()
            await asyncio.sleep(SCAN_TIMEOUT)
            await scanner.stop()
            return discovered

        return asyncio.run(_async_scan())
    except Exception as exc:  # pragma: no cover
        _LOGGER.warning("BLE scan failed: %s", exc)
        return []


class IPixelColorCoordinator:
    """Manages the BLE connection and command dispatch for a single device."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        name: Optional[str] = None,
    ) -> None:
        self.hass = hass
        self.address = address
        self._name = name or f"iPixel Color {address}"
        self._client: Optional[pypixelcolor.AsyncClient] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._should_reconnect = False
        self.is_on = True
        self.brightness: int = DEFAULT_BRIGHTNESS
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return self._name

    async def _ensure_connected(self) -> None:
        """Connect the BLE client if not already connected."""
        if self._client is not None:
            try:
                await self._client.connect()
                return
            except Exception:
                self._client = None
        self._client = pypixelcolor.AsyncClient(self.address)
        await self._client.connect()

    async def _auto_reconnect(self) -> None:
        """Continuously attempt to reconnect when the connection drops."""
        while self._should_reconnect:
            try:
                _LOGGER.debug("Attempting reconnect to %s", self.address)
                self._client = pypixelcolor.AsyncClient(self.address)
                await self._client.connect()
                _LOGGER.info("Reconnected to %s", self.address)
                return
            except Exception as exc:
                _LOGGER.warning("Reconnect failed for %s: %s", self.address, exc)
                await asyncio.sleep(5)

    async def _async_command(
        self,
        command: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        **kwargs,
    ) -> None:
        """Execute a BLE command with automatic reconnection."""
        async with self._lock:
            await self._ensure_connected()
            try:
                await command(*args, **kwargs)
            except Exception as exc:
                _LOGGER.error("Command failed: %s", exc)
                self._client = None
                raise

    # ── send_text (wraps pypixelcolor AsyncClient.send_text) ──────────────
    async def async_send_text(
        self,
        text: str,
        color: str = DEFAULT_COLOR,
        rainbow_mode: int = 0,
        animation: int = DEFAULT_ANIMATION,
        speed: int = DEFAULT_SPEED,
        save_slot: int = 0,
    ) -> None:
        """Send text to the LED matrix."""
        await self._async_command(
            self._client.send_text,
            text,
            rainbow_mode=rainbow_mode,
            save_slot=save_slot,
            speed=speed,
            color=color,
        )
        self.is_on = True

    # ── send_image (wraps pypixelcolor AsyncClient.send_image) ────────────
    # Confirmed signature from pypixelcolor v0.4.0:
    #   def send_image(path: Union[str, Path],
    #                  resize_method: Union[str, ResizeMethod] = ResizeMethod.CROP,
    #                  device_info: Optional[DeviceInfo] = None,
    #                  save_slot: int = 0)
    async def async_send_image(
        self,
        image: str,
        save_slot: int = 0,
        animation: int = 0,
        speed: int = DEFAULT_SPEED,
        resize_method: str = DEFAULT_RESIZE_METHOD,
    ) -> None:
        """Send a static image or animated GIF to the LED matrix.
        
        Args:
            image:     Full path to a local image file (PNG, JPG, WebP, BMP,
                       TIFF, GIF, HEIC/HEIF are supported by pypixelcolor).
            save_slot: Save slot (1-10) to persist on device. 0=transient.
            animation: Reserved; passed through but not used by the library.
            speed:     Reserved; passed through but not used by the library.
            resize_method: 'crop' (fill area, crop edges) or 'fit' (fit with
                           black padding). Maps to pypixelcolor.ResizeMethod.
        """
        await self._async_command(
            self._client.send_image,
            image,
            resize_method=resize_method,
            save_slot=save_slot,
        )
        self.is_on = True

    # ── send_image_hex (wraps pypixelcolor AsyncClient.send_image_hex) ────
    # Confirmed signature from pypixelcolor v0.4.0:
    #   def send_image_hex(hex_string: Union[str, bytes],
    #                      file_extension: str,
    #                      resize_method: Union[str, ResizeMethod] = ResizeMethod.CROP,
    #                      device_info: Optional[DeviceInfo] = None,
    #                      save_slot: int = 0)
    async def async_send_image_hex(
        self,
        hex_string: str,
        file_extension: str = ".png",
        save_slot: int = 0,
        resize_method: str = DEFAULT_RESIZE_METHOD,
    ) -> None:
        """Send an image from a hexadecimal string representation.
        
        Args:
            hex_string:     Hexadecimal string of raw image data.
            file_extension: File extension identifying the image type
                            (e.g. '.png', '.gif').
            save_slot:      Save slot (1-10). 0=transient.
            resize_method:  'crop' or 'fit'.
        """
        await self._async_command(
            self._client.send_image_hex,
            hex_string,
            file_extension,
            resize_method=resize_method,
            save_slot=save_slot,
        )
        self.is_on = True

    # ── Power & brightness ─────────────────────────────────────────────────
    async def async_set_power(self, on: bool) -> None:
        if self._client is not None:
            try:
                await self._client.set_power(on)
            except Exception as exc:
                _LOGGER.error("set_power failed: %s", exc)
                raise
        self.is_on = on

    async def async_set_brightness(self, brightness: int) -> None:
        if self._client is not None:
            try:
                await self._client.set_brightness(brightness)
            except Exception as exc:
                _LOGGER.error("set_brightness failed: %s", exc)
                raise
        self.brightness = brightness

    async def async_disconnect(self) -> None:
        """Stop reconnect loop and disconnect."""
        self._should_reconnect = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None

    @staticmethod
    def discover() -> list[dict]:
        """Return a list of discovered devices as {address, name} dicts."""
        raw = _scan_for_devices()
        return [{"address": addr, "name": name} for addr, name in raw.items()]
