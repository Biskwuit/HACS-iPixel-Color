"""Config flow for iPixel Color LED Matrix."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import bleakex
import voluptuous as vol

from homeassistant.components.bluetooth import (
    async_discovered_service_info,
    BluetoothScrolling,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from .const import (
    CONF_ADDRESS as CONF_ADDR,
    CONF_NAME as CONF_DEV_NAME,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Known iPixel device name prefixes (BLE advertise name starts with this)
IPIXEL_NAME_PREFIXES = ("PixelColor", "iPixel", "LEDMatrix", "MATRIX", "IPixel")


def _looks_like_ipixel_device(name: str | None) -> bool:
    """Return True if the BLE name looks like an iPixel device."""
    if not name:
        return False
    upper = name.upper()
    return any(prefix.upper() in upper for prefix in IPIXEL_NAME_PREFIXES)


class IPixelColorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for iPixel Color LED Matrix.

    Two paths:
      1. Auto-discover (BLE scan) — list nearby iPixel devices for user to pick.
      2. Manual — user enters a BLE MAC address directly.
    """

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Step: user — pick discovery method or manual entry
    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Present two options: Auto-discover or Manual entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            choice = user_input.get("selection")
            if choice == "scan":
                return await self.async_step_scan()
            if choice == "manual":
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("selection", default="scan"): vol.In({
                    "scan": "Auto-discover nearby iPixel devices",
                    "manual": "Enter address manually",
                }),
            }),
            errors=errors,
            description_placeholders={},
        )

    # ------------------------------------------------------------------
    # Step: scan — BLE scan, list iPixel devices
    # ------------------------------------------------------------------
    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Scan for BLE devices and let user pick one."""
        errors: dict[str, str] = {}

        try:
            _LOGGER.info("Starting BLE scan for iPixel devices...")
            discovered: list[dict[str, Any]] = []

            def _make_device_entry(device: bleakex.BLEDevice) -> dict[str, Any] | None:
                name = device.name or device.address
                if not _looks_like_ipixel_device(name):
                    return None
                return {
                    "address": device.address,
                    "name": name,
                    "rssi": getattr(device, "rssi", None),
                }

            # Scan for 10 seconds
            scan_iter = bleakex.BleakScanner.discover(timeout=10.0)
            seen: set[str] = set()
            async for device in scan_iter:
                if device.address in seen:
                    continue
                seen.add(device.address)
                entry = _make_device_entry(device)
                if entry:
                    discovered.append(entry)

            self._discovered_devices = discovered

            if not discovered:
                return self.async_show_form(
                    step_id="scan",
                    data_schema=vol.Schema({}),
                    errors={"base": "no_devices_found"},
                    description_placeholders={},
                )

            # Build selection schema
            choices = {
                d["address"]: f"{d['name']} ({d['address']})"
                + (f" [RSSI {d['rssi']}]" if d["rssi"] is not None else "")
                for d in discovered
            }

            if user_input is not None:
                address = user_input.get(CONF_ADDRESS)
                if address and address in choices:
                    device = next(d for d in discovered if d["address"] == address)
                    return await self._async_create_entry(
                        device["address"], device.get("name") or DEFAULT_NAME
                    )

            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema({
                    vol.Required(CONF_ADDRESS): vol.In(choices),
                }),
                errors=errors,
                description_placeholders={},
            )

        except Exception as ex:
            _LOGGER.exception("BLE scan error: %s", ex)
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema({}),
                errors={"base": "bluetooth_error"},
                description_placeholders={"error": str(ex)},
            )

    # ------------------------------------------------------------------
    # Step: manual — user enters BLE MAC address
    # ------------------------------------------------------------------
    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let user type in a BLE address directly."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input.get(CONF_ADDRESS, "").strip()
            name = user_input.get(CONF_DEV_NAME, "").strip() or DEFAULT_NAME

            if not address:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                # Validate by attempting a brief connect
                try:
                    import pypixelcolor
                    client = pypixelcolor.AsyncClient(address)
                    await client.connect()
                    await client.disconnect()
                except Exception as ex:
                    _LOGGER.warning("Manual address validation failed: %s", ex)
                    errors["base"] = "cannot_connect"
                    errors["address"] = str(ex)

                if not errors:
                    return await self._async_create_entry(address, name)

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): str,
                vol.Optional(CONF_DEV_NAME, default=DEFAULT_NAME): str,
            }),
            errors=errors,
            description_placeholders={},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _async_create_entry(
        self, address: str, name: str
    ) -> ConfigFlowResult:
        """Create the config entry after validating the device."""
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=name,
            data={
                CONF_ADDRESS: address,
                CONF_DEV_NAME: name,
            },
        )
