"""Constants for the iPixel Color integration."""

DOMAIN = "ipixel_color"

CONF_ADDRESS = "address"
CONF_NAME = "name"

DEFAULT_NAME = "iPixel Color Matrix"

PLATFORMS = ["light"]

RECONNECT_DELAY = 5
MAX_RECONNECT_ATTEMPTS = 3

SERVICE_SEND_TEXT = "send_text"
SERVICE_SEND_IMAGE = "send_image"
SERVICE_SET_CLOCK = "set_clock"
SERVICE_SHOW_SLOT = "show_slot"
SERVICE_SET_ORIENTATION = "set_orientation"
SERVICE_CLEAR = "clear"