"""Constants for the iPixel Color integration."""

DOMAIN = "ipixel_color"

# Service names
SERVICE_SEND_TEXT = "send_text"
SERVICE_SEND_IMAGE = "send_image"
SERVICE_SEND_IMAGE_HEX = "send_image_hex"

# BLE scanning
SCAN_TIMEOUT = 15
ADAPTER = "hci0"

# Defaults
DEFAULT_NAME = "iPixel Color"
DEFAULT_BRIGHTNESS = 128
DEFAULT_SPEED = 80
DEFAULT_COLOR = "ffffff"
DEFAULT_ANIMATION = 1
DEFAULT_RESIZE_METHOD = "crop"

# Device name prefix used by iPixel Color BLE advertisements
IPIXEL_ADVERTISEMENT_NAME_PREFIX = "iPixel"
