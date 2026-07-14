# iPixel Color LED Matrix — Home Assistant Custom Integration

A **HACS-compatible** Home Assistant integration for the **iPixel Color LED Matrix** (also sold as "PixelColor" or "iPixel"). Communicates with the device over Bluetooth Low Energy (BLE).

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation via HACS](#installation-via-hacs)
4. [Manual Installation](#manual-installation)
5. [Configuration](#configuration)
   - [Auto-Discover](#1-auto-discover)
   - [Manual Entry](#2-manual-entry)
6. [Entities & Services](#entities--services)
   - [Light Entity](#light-entity)
   - [Services](#services)
7. [Auto-Reconnect Behaviour](#auto-reconnect-behaviour)
8. [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Details |
|---|---|
| **Auto-Discovery** | Scans for nearby BLE iPixel devices and lists them with RSSI |
| **Manual Entry** | Enter any BLE MAC address if discovery does not work |
| **Light Entity** | Power on/off and brightness control (0–100 → 0–255) |
| **send_text Service** | Display custom text with colour, background, animation, speed, font, rainbow mode |
| **send_image Service** | Display PNG/WebP/JPG/BMP/GIF/HEIC images |
| **Auto-Reconnect** | Exponential-backoff reconnect loop (5 s → 60 s cap) runs forever in the background |
| **Bluetooth Integration** | Registers with HA's native Bluetooth discovery if the device advertises nearby |

---

## Requirements

- Home Assistant OS or Supervised (running HA core ≥ 2024.1)
- **Bluetooth adapter** on the Home Assistant host
- Python ≥ 3.10 with `pip install pypixelcolor` available to HA
- The iPixel device must be powered on and **not paired** to another phone/computer

> ⚠️ Only one BLE connection is possible at a time. If the device is already connected to a phone, HA will not be able to connect. Unpair it first.

---

## Installation via HACS

1. Add this repository as a **custom repository** in HACS:
   - Open **HACS → Integrations → ⋯ → Custom repositories**
   - Paste the GitHub repository URL
   - Select category **Integration**
   - Click **Add**
2. Search for **"iPixel Color LED Matrix"** and install
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → + Add Integration**
5. Select **"iPixel Color LED Matrix"**

---

## Manual Installation

```bash
# Copy the custom_components folder to your HA config
cp -r custom_components/ipixel_color /config/custom_components/
# or use a symlink
ln -s /path/to/this/repo/custom_components/ipixel_color /config/custom_components/
```

Then restart HA and add the integration as above.

---

## Configuration

Two setup flows are offered:

### 1. Auto-Discover

- The integration scans for BLE devices for up to **10 seconds**
- Devices whose advertise name starts with `PixelColor`, `iPixel`, `LEDMatrix`, `MATRIX`, or `IPixel` are listed
- Each discovered device shows its **MAC address** and **RSSI signal strength**
- Pick the correct device and confirm

### 2. Manual Entry

If auto-discover does not find your device:

1. Select **"Enter address manually"**
2. Enter the **BLE MAC address** (e.g. `AA:BB:CC:DD:EE:FF`)
3. Optionally give the device a friendly name
4. The integration will attempt a test connection before saving

---

## Entities & Services

### Light Entity

Once configured, a `light` entity is created (e.g. `light.ipixel_color_aa_bb_cc_dd_ee_ff`).

**Attributes exposed:**

| Attribute | Description |
|---|---|
| `brightness` | Current brightness 0–255 |
| `available` | `True` when BLE is connected |

**Standard light controls:**

- **Turn On / Turn Off** — calls `set_power(True/False)`
- **Brightness slider** — maps 0–255 HA brightness to 0–100 device brightness

---

### Services

#### `ipixel_color.send_text`

Send a text message to the matrix.

| Field | Type | Default | Description |
|---|---|---|---|
| `entity_id` | string | *required* | The light entity ID |
| `message` | string | *required* | Text to display |
| `color` | string | `ffffff` | Hex text colour (no `#`) |
| `bg_color` | string | none | Hex background colour |
| `animation` | int | `0` | Animation type 0–7 (not 3 or 4) |
| `speed` | int | `80` | Speed 0–100 |
| `rainbow_mode` | int | `0` | Rainbow mode 0–9 (0=off) |
| `font` | string | `CUSONG` | Font: `CUSONG`, `SIMSUN`, `VCR_OSD_MONO` |
| `brightness` | int | — | Temporary brightness override 0–100 |

**Built-in fonts:**

- `CUSONG` — custom decorative font (default)
- `SIMSUN` — standard sans-serif
- `VCR_OSD_MONO` — monospace retro font

#### `ipixel_color.send_image`

Display a local image file.

| Field | Type | Default | Description |
|---|---|---|---|
| `entity_id` | string | *required* | The light entity ID |
| `path` | string | *required* | Full path to image file on the HA host |
| `resize_method` | string | `crop` | `crop` fills the display and crops excess; `fit` fits whole image with black padding |

**Supported formats:** PNG, WebP, JPG, BMP, TIFF, GIF, HEIC/HEIF (if `pillow-heif` is installed).

---

## Auto-Reconnect Behaviour

If the BLE connection drops:

1. The light entity immediately shows **Unavailable**
2. A background reconnect loop starts with **exponential backoff**:
   - 1st retry after **5 s**
   - 2nd retry after **10 s**
   - 3rd retry after **20 s**
   - 4th retry after **40 s**
   - All subsequent retries every **60 s** (cap)
3. As soon as the device reconnects, the light becomes available again and the next command is sent
4. The loop runs **forever** while the integration is loaded (it only stops when you remove the integration from HA)

Disconnection can happen because:
- The device goes out of Bluetooth range
- The device is switched off
- Another phone/tablet connects to the device

> 💡 The reconnect loop is **non-blocking** — Home Assistant remains fully responsive while retries are in progress.

---

## Troubleshooting

### "Device not found" / "Cannot connect"
- Make sure the device is **powered on**
- Make sure it is **not paired** to any phone/computer (BLE allows only one connection at a time)
- Move closer to the device
- Restart the Bluetooth service on your HA host (`systemctl restart bluetooth` on Linux)

### Persistent connection issues with bleak 2.x
The `bleak` BLE library version 2.0.x has known issues on some systems (see [pypixelcolor issue #58](https://github.com/lucagoc/pypixelcolor/issues/58)). If you see errors like:
```
Failed to enable response notifications: [org.freedesktop.DBus.Error.UnknownObject] ...
```
Try downgrading bleak:
```bash
pip install bleak==1.1.1
```

### Multiple devices not responding simultaneously
Heavy data operations (images) on **multiple devices at the same time** are not stable due to Bluetooth backend limitations. Send to one device, wait briefly, then send to the next.

---

## API Reference (from pypixelcolor library)

The integration wraps these **real** methods from [`pypixelcolor.AsyncClient`](https://lucagoc.fr/pypixelcolor/latest/reference/async_client/):

| Method | Description |
|---|---|
| `AsyncClient(address)` | Constructor takes a BLE MAC address string |
| `await client.connect()` | Connect to the device; retrieves device info |
| `await client.disconnect()` | Gracefully disconnect |
| `await client.set_power(on: bool)` | Power on/off |
| `await client.set_brightness(level: int)` | Set brightness 0–100 |
| `await client.set_orientation(orientation: int)` | Set orientation 0–3 |
| `await client.send_text(text, ...)` | Display text with styling options |
| `await client.send_image(path, ...)` | Display an image file |
| `await client.clear()` | Clear the display |
| `await client.get_device_info()` | Get cached device info (width/height/type) |

Discovery is performed via `bleakex.BleakScanner.discover()` filtered by known BLE name prefixes.

---

## Limitations

- **No HA state restoration**: After a HA restart, the light entity defaults to `off`. Reconnection happens automatically.
- **Single device connection**: Each iPixel device can only hold one BLE connection; do not pair it with a phone while HA is using it.
- **Images must be on the HA host**: The `send_image` service requires the file path on the machine running HA, not a URL.
- **No HA Bluetooth auto-popup without matching service UUID**: The manifest includes a service UUID matcher (`0000fa02-0000-1000-8000-00805f9b34fb`) and manufacturer ID (4729) to trigger HA's built-in Bluetooth prompt when the device advertises — this works on HA 2024.1+ with the Bluetooth integration enabled.

---

## Credit

Built using the [`pypixelcolor`](https://github.com/lucagoc/pypixelcolor) Python library by [lucagoc](https://github.com/lucagoc).
