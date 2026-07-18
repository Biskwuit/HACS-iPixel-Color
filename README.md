# iPixel Color LED Matrix for Home Assistant

A Home Assistant custom integration (HACS extension) for controlling iPixel Color LED Matrix devices via Bluetooth Low Energy (BLE).

## Features

- **Light Entity**: Control power (on/off) and brightness
- **Text Entity**: Send custom messages to the LED matrix display
- **Auto-Discovery**: Automatically discovers iPixel Color devices via Bluetooth
- **Auto-Reconnect**: Automatically reconnects if the connection is lost
- **Multiple Devices**: Support for multiple iPixel Color devices

## Requirements

- Home Assistant 2024.1 or later
- Python 3.10+
- A Bluetooth adapter
- iPixel Color LED Matrix device

## Installation

### Via HACS (Recommended)

1. Open Home Assistant and go to HACS
2. Go to Integrations
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/your-username/ipixel_color`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "iPixel Color" and install

### Manual Installation

1. Copy the `custom_components/ipixel_color` folder to your Home Assistant's `config/custom_components/` folder
2. Restart Home Assistant

## Configuration

### Automatic Discovery

1. Power on your iPixel Color LED Matrix device
2. Go to Home Assistant → Settings → Devices & Services
3. Click "Add Integration"
4. Search for "iPixel Color LED Matrix"
5. Select your device from the list

### Manual Configuration (YAML)

```yaml
# configuration.yaml (not typically needed - use UI config flow)
```

## Usage

### Light Entity

Once configured, you'll get a light entity that allows you to:
- Turn the LED matrix on/off
- Adjust brightness (0-100%)

### Text Entity

The text entity allows you to send messages to the display:
- In Home Assistant, go to the device page
- Use the text entity to send custom messages
- Messages will display on your LED matrix

### Services

The integration exposes the following services:

#### `ipixel_color.send_text`

Send custom text to the LED matrix.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | The text entity ID |
| `text` | string | The text message to display |
| `animation` | integer | Animation type (0-7, default: 0) |
| `speed` | integer | Animation speed 0-100 (default: 80) |
| `color` | string | Hex color code (default: "ffffff" for white) |

Example:
```yaml
service: ipixel_color.send_text
data:
  entity_id: text.ipixel_color_led_matrix_text
  text: "Hello World!"
  animation: 1
  speed: 50
```

#### `ipixel_color.set_brightness`

Set the brightness level.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | The light entity ID |
| `brightness` | integer | Brightness level 0-100 |

## Troubleshooting

### Device Not Found

1. Ensure the device is powered on
2. Ensure the device is not connected to another phone/computer (only one BLE connection at a time)
3. Try moving closer to the device
4. Restart the Bluetooth service on your Home Assistant host

### Connection Issues

If you experience persistent connection issues, try downgrading bleak:

```bash
pip uninstall bleak
pip install bleak==1.1.1
```

## Supported Devices

Tested with:
- iPixel Color LED Matrix (various models)

Likely supports other iPixel Color variants using the same BLE protocol.

## Credits

- Uses the [pypixelcolor](https://github.com/lucagoc/pypixelcolor) Python library by lucagoc

## License

MIT License
