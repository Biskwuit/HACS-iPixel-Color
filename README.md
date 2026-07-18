# iPixel Color LED Matrix — Home Assistant Integration

[![hacs](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/your-github-username/hacs-ipixel-color)](https://github.com/your-github-username/hacs-ipixel-color/releases)

A Home Assistant custom integration for the **iPixel Color** LED matrix display, controlled via Bluetooth Low Energy (BLE). Built on top of [`pypixelcolor`](https://github.com/lucagoc/pypixelcolor).

## Features

- **Bluetooth auto-discovery** of nearby iPixel Color devices.
- **Power, brightness, and orientation** control as a standard Home Assistant light entity.
- **Text display** with fonts, colors, rainbow modes, and slide animations.
- **Image / GIF display** from local file paths.
- **Hex image sending** for pre-encoded image data.
- **Automatic reconnection** on BLE link drop.
- **Service calls** for automation (send text, send image, send image from hex).

## Supported Devices

Tested with iPixel Color LED matrix panels. The integration auto-detects device dimensions (16×16, 32×32, etc.) via BLE device-info queries.

## Installation

### Via HACS (Recommended)

1. Install [HACS](https://hacs.xyz) if not already installed.
2. Add this repository as a **Custom Repository** in HACS → ⋮ → Custom repositories:
   - Repository: `https://github.com/your-github-username/hacs-ipixel-color`
   - Category: `Integration`
3. Install the **iPixel Color LED Matrix** integration from the HACS store.
4. Restart Home Assistant.
5. Add the integration via **Settings → Devices & Integrations → Add Integration → iPixel Color**.

### Manual Installation

Copy the `custom_components/ipixel_color/` folder into your Home Assistant's `custom_components/` directory, then restart.

## Configuration

After installation, use the UI flow:

1. **Settings → Devices & Integrations → Add Integration → iPixel Color**.
2. The integration will scan for nearby BLE devices advertising the iPixel Color service.
3. Select your device from the list (discovered by BLE address).
4. Assign an Area (optional) and confirm.

No YAML configuration is required for this integration.

## Services

All services target `ipixel_color` and operate on the discovered light entity.

### `ipixel_color.send_text`

Display text on the LED matrix.

| Parameter | Type   | Default | Description                                      |
|-----------|--------|---------|--------------------------------------------------|
| `text`    | string | *required* | Text to display. Max 500 chars.             |
| `color`   | string | `ffffff` | 6-digit hex color (e.g. `ff0000` = red).      |
| `rainbow_mode` | int | `0`   | Rainbow gradient mode (0=off, 1–9 = mode).      |
| `animation` | int  | `1`   | Text slide animation (1=right, 2=left, 3=up, 4=down). |
| `speed`   | int    | `80`   | Animation speed 0–100.                           |
| `save_slot` | int  | `0`    | Save slot (1–10) to persist text on device.   |

```yaml
service: ipixel_color.send_text
data:
  text: "Hello, Home Assistant!"
  color: "00ff88"
  animation: 1
  speed: 80
```

### `ipixel_color.send_image`

Display a static image or animated GIF from a local file path.

| Parameter | Type   | Default | Description                                      |
|-----------|--------|---------|--------------------------------------------------|
| `image`   | string | *required* | Full path to the image file. Supports PNG, JPG, WebP, BMP, TIFF, GIF, HEIC/HEIF. |
| `save_slot` | int  | `0`    | Save slot (1–10).                                |
| `animation` | int  | `0`   | Reserved for animation control. Currently unused. |
| `speed`   | int    | `80`   | Reserved for playback speed. Currently unused.   |
| `resize_method` | string | `crop` | `crop` (fill area, crop edges) or `fit` (fit with black padding). |

```yaml
service: ipixel_color.send_image
data:
  image: "/config/www/heart.png"
  resize_method: "crop"
```

### `ipixel_color.send_image_hex`

Display an image from a hexadecimal string representation of image data.

| Parameter   | Type   | Default   | Description                              |
|-------------|--------|-----------|------------------------------------------|
| `hex_string`| string | *required*| Hexadecimal string of image data.        |
| `file_extension` | string | *required* | File extension (e.g. `.png`, `.gif`). |
| `save_slot` | int    | `0`       | Save slot (1–10).                        |
| `resize_method` | string | `crop` | `crop` or `fit`.                      |

```yaml
service: ipixel_color.send_image_hex
data:
  hex_string: "89504e470d..."
  file_extension: ".png"
  save_slot: 0
```

## BLE Requirements

This integration requires a Bluetooth adapter reachable by the Home Assistant host (either a local Bluetooth adapter or a Bluetooth proxy). The iPixel Color device must be powered on and in BLE advertising range.

## Dependencies

- Python ≥ 3.9
- `pypixelcolor ≥ 0.4.0`
- `bleak ≥ 0.21.0`
- `Pillow` (for image processing)

These are automatically installed when installing via HACS.

## Troubleshooting

### Device not found during setup
- Make sure the iPixel Color device is powered on and in range.
- Ensure the host machine has an active Bluetooth adapter.
- Check Home Assistant logs for BLE scanning errors.

### Image looks stretched
- Use `resize_method: fit` to add black padding instead of cropping.

### Connection drops
- The integration implements automatic reconnection. If drops persist, ensure the device is within reliable BLE range.

## Contributing

Issues and pull requests are welcome at [github.com/your-github-username/hacs-ipixel-color](https://github.com/your-github-username/hacs-ipixel-color).

## License

MIT License
