"""Constants for the iPixel Color LED Matrix integration."""

from enum import Enum

DOMAIN = "ipixel_color"

# Connection retry constants
CONF_ADDRESS = "address"
CONF_NAME = "name"
DEFAULT_NAME = "iPixel Color LED Matrix"

# Retry/backoff delays in seconds
RECONNECT_BASE_DELAY = 5.0
RECONNECT_MAX_DELAY = 60.0
RECONNECT_BACKOFF_FACTOR = 2.0

# pypixelcolor service UUIDs (confirmed from source: lib/constants.py)
WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"

# Bleak exceptions to catch for reconnects
BLEAK_EXCEPTIONS = (
    Exception,
)  # bleakex.BleakError is a subclass of Exception; import dynamically

# Brightness range
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 100


class Orientation(str, Enum):
    """Device orientation values (0-3)."""

    NORMAL = "Normal"
    ROTATE_90 = "90° clockwise"
    ROTATE_180 = "180°"
    ROTATE_270 = "270° clockwise"

    @property
    def value_int(self) -> int:
        mapping = {
            "Normal": 0,
            "90° clockwise": 1,
            "180°": 2,
            "270° clockwise": 3,
        }
        return mapping[self.name]

    @property
    def display_name(self) -> str:
        return self.name


ORIENTATION_MAP = {
    0: "Normal",
    1: "90° clockwise",
    2: "180°",
    3: "270° clockwise",
}
