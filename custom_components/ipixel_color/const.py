"""Constants for the iPixel Color LED Matrix integration."""

DOMAIN = "ipixel_color"

CONF_ADDRESS = "address"

DEFAULT_SCAN_INTERVAL = 30
RECONNECT_DELAY = 10
RECONNECT_MAX_DELAY = 120

# Device info keys
ATTR_DEVICE_WIDTH = "width"
ATTR_DEVICE_HEIGHT = "height"
ATTR_DEVICE_MODEL = "model"
ATTR_DEVICE_FIRMWARE = "firmware"

# Service UUID for iPixel Color (if known)
# If the device doesn't match, you may need to adjust this.
# Common approach: use manufacturer data or service UUID.
# NOTE: Verify this UUID against your device's BLE advertisement.
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"