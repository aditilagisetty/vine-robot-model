# Vine Robot Pressure Sensing

Reads a Honeywell ABP pressure sensor over I2C with a Raspberry Pi Pico, calibrates its zero point at startup, and streams pressure in psi over USB serial in [Teleplot](https://marketplace.visualstudio.com/items?itemName=alexnesnes.teleplot) format for live graphing.

This is the single-sensor test stage of the vine robot's pressure sensing. The code is structured so more sensors can be added later through an I2C multiplexer.

See [REQUIREMENTS.md](REQUIREMENTS.md) for the parts list, software, and project settings.

## Wiring

| Sensor pin | Function | Pico pin |
|---|---|---|
| 1 | GND | GND (pin 38 or pin 3) |
| 2 | V<sub>supply</sub> (3.3 V) | 3V3 (OUT), pin 36 |
| 3 | INT | not connected |
| 4 | NC | not connected |
| 5 | SDA | GP4, pin 6 |
| 6 | SCL | GP5, pin 7 |

Plus a **4.7 kΩ pull-up** from SDA to 3.3 V and another from SCL to 3.3 V.

### Identifying pin 1

- **Top (port side):** pin 1 is the leg next to the small notch on the body.
- **Bottom:** pin 1 has the pad with the cut-off corner.
- Pins number in a U shape: 1, 2, 3 down one side, then 4, 5, 6 back up the other. **Pin 6 is directly across from pin 1.**

### Warnings

- **The sensor is not reverse-polarity protected.** Swapping pins 1 and 2 can destroy it. Check them before plugging in USB.
- **Don't use 3V3_EN (pin 37), VSYS (pin 39), or VBUS (pin 40)** for sensor power. Only 3V3 (OUT), pin 36.
- **Don't block the gauge reference hole** on the bottom of the sensor. Leave a small gap between the sensor and the breadboard.
- The sensor's two rows of legs are about 11 mm apart, which doesn't match breadboard spacing. Straddle the center channel (columns d and f) and squeeze the legs inward slightly.

## Building and running

1. Open the project in VS Code with the Raspberry Pi Pico extension.
2. Hold **BOOTSEL** while plugging in the Pico (it appears as a drive named **RPI-RP2**).
3. Click **Run**. The Pico reboots into the program.
4. Open **Teleplot** in VS Code, select the Pico's serial port, and click **Open**. (The Serial Monitor also works if you just want the raw text, but only one of them can have the port open at a time.)

**Keep the sensor's port open to room air when the Pico starts.** The program measures the zero point during startup.

### Expected output

Each reading is printed as a Teleplot line, which Teleplot turns into a live graph named `pressure`:

```
>pressure:0.000
>pressure:-0.001
>pressure:0.000
```

Any line starting with `>` followed by `name:value` becomes a plot. To add another trace (for example, a second sensor), print another name, like `>pressure2:0.123`.

At room air, readings should sit within a few thousandths of 0 psi. To test with pressure, push tubing onto the barbed port and blow gently or use a syringe. Blowing toward an open port won't register, because no pressure builds up without a seal.

## How it works

### Reading the sensor (`read_raw_count`)

The sensor sends 2 bytes:

```
        buf[0]                       buf[1]
[S1 S0 P13 P12 P11 P10 P9 P8]   [P7 P6 P5 P4 P3 P2 P1 P0]
 status  └─ top 6 bits ─┘        └──── bottom 8 bits ────┘
```

- **Status** = `buf[0] >> 6`. Only `00` (fresh, valid data) is accepted. `10` means stale data (read before the sensor updated).
- **Counts** = `((buf[0] & 0x3F) << 8) | buf[1]`, a 14-bit value from 0 to 16383.

### Zero calibration (`offset_calc`)

At startup, the program takes 101 readings 10 ms apart, sorts the good ones with `qsort`, and uses the **median** as the zero point. The median ignores occasional spikes. Calibration fails if fewer than half the readings succeed.

### Converting to psi (`transfer_func`)

From the datasheet, the sensor outputs 10% of 2<sup>14</sup> counts (1638) at 0 psi and 90% (14745) at 5 psi, a span of 13107 counts. The program replaces the datasheet's 1638 with the measured zero point:

```
psi = (counts − offset) / 13107 × (Pmax − Pmin) + Pmin
```

Only the zero point is calibrated. The span (13107) is factory-calibrated and taken from the datasheet.

### Sensor settings (`pressure_sensor_t`)

Each sensor is described by a struct holding its I2C controller, address, multiplexer channel (for later), pressure range, and measured offset, so the same functions work for any number of sensors.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| No COM port appears | `pico_enable_stdio_usb` is 0, wrong `PICO_BOARD`, or a charge-only USB cable |
| RPI-RP2 drive doesn't disappear after flashing | `.uf2` built for the wrong board (must be `pico`) |
| "Can't get pressure" every reading | Wiring: check SDA/SCL rows, pull-ups, and power |
| "Too many failed readings" at startup | Sensor not responding during calibration; check wiring |
| Readings drift right after power-on | Normal sensor warm-up; wait a couple of seconds before calibrating |
| Readings stuck near 0 when blowing on it | No seal; use tubing on the barbed port |
| Teleplot shows no graph | Serial Monitor still has the port open (close it), or lines are missing the `>` prefix or `\n` |
| Sensor gets warm | **Unplug immediately**: power and ground are reversed |
| Build error: implicit declaration of `qsort` | Add `#include <stdlib.h>` |

## Next steps

- Add the **TCA9548A multiplexer** so all six sensors (which share address `0x28`) can be read, using the `mux_channel` field.
- Move the sensor functions into `pressure_sensor.c` / `pressure_sensor.h`.
