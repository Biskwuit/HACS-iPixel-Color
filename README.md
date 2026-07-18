# iPixel Color LED Matrix for Home Assistant

Custom Home Assistant integration for iPixel Color LED Matrix devices using `pypixelcolor`.

## Features

- Bluetooth auto-discovery
- Manual BLE address setup
- Automatic reconnect on command failure
- Light entity
- Brightness control
- Power on/off
- Send text service
- Clock mode service
- Show saved slot service
- Orientation service

## Installation with HACS

1. Open HACS.
2. Go to Integrations.
3. Click the three-dot menu.
4. Choose Custom repositories.
5. Add this repository URL.
6. Category: Integration.
7. Install `iPixel Color LED Matrix`.
8. Restart Home Assistant.
9. Go to Settings > Devices & services.
10. Add `iPixel Color`.

## Services

### Send text

```yaml
service: ipixel_color.send_text
target:
  entity_id: light.ipixel_color_matrix
data:
  text: "Hello!"
  color: "ff0000"
  speed: 80