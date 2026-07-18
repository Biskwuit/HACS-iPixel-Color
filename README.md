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
- Send image (file or hex data) service
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
```

### Send image

Send an image from a file path:

```yaml
service: ipixel_color.send_image
target:
  entity_id: light.ipixel_color_matrix
data:
  path: "/config/www/logo.png"
  resize_method: "crop"
```

Send an image from hex data:

```yaml
service: ipixel_color.send_image
target:
  entity_id: light.ipixel_color_matrix
data:
  hex_string: "89504E470D0A1A0A0000000D49484452000000100000001008020000009001A..."
  file_extension: ".png"
  resize_method: "fit"
```

Supported image formats: PNG, JPG, GIF, WebP, BMP, TIFF, HEIC, HEIF.

### Clock mode

```yaml
service: ipixel_color.set_clock
target:
  entity_id: light.ipixel_color_matrix
data:
  style: 1
  show_date: true
  format_24: true
```

### Show slot

```yaml
service: ipixel_color.show_slot
target:
  entity_id: light.ipixel_color_matrix
data:
  number: 1
```

## Example automations

### Show doorbell message on iPixel

```yaml
alias: Show doorbell message on iPixel
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.doorbell
    to: "on"
action:
  - service: ipixel_color.send_text
    target:
      entity_id: light.ipixel_color_matrix
    data:
      text: "Doorbell!"
      color: "00ff00"
      animation: 0
      speed: 80
```

### Display weather icon

```yaml
alias: Show weather icon on iPixel
mode: single
trigger:
  - platform: state
    entity_id: sensor.weather_icon
action:
  - service: ipixel_color.send_image
    target:
      entity_id: light.ipixel_color_matrix
    data:
      path: "/config/www/weather/{{ states('sensor.weather_icon') }}.png"
      resize_method: "crop"
```

## Notes

This integration uses BLE. Your Home Assistant host must have a working Bluetooth adapter.

## Example automation

```yaml
alias: Show doorbell message on iPixel
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.doorbell
    to: "on"
action:
  - service: ipixel_color.send_text
    target:
      entity_id: light.ipixel_color_matrix
    data:
      text: "Doorbell!"
      color: "00ff00"
      animation: 0
      speed: 80
```

---

### Important notes

- This is a **custom integration**, not a Home Assistant core PR-ready integration.
- BLE device names vary, so if auto-discovery does not catch your device, use **manual setup** with its BLE address.
- The integration uses `pypixelcolor.client.AsyncClient`, whose docs show async methods including `connect`, `disconnect`, `send_text`, `send_image`, `send_image_hex`, `set_brightness`, `set_power`, `set_clock_mode`, `show_slot`, and more. ([lucagoc.fr](https://lucagoc.fr/pypixelcolor/latest/reference/async_client/))
- `pypixelcolor` is third-party and not official iPixel Color software, as stated by its docs. ([lucagoc.fr](https://lucagoc.fr/pypixelcolor/latest/))