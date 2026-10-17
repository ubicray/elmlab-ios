#!/usr/bin/env python3
"""Saved experiment states with plausible measurements, for the App Store screenshots.

    make_states.py OUTPUT_DIR

The simulator has no motion sensors, so the screenshots open these instead: the bundled
experiment with its containers filled in (the format the app's own "save state" writes) and its
sensor marked ignoreUnavailable, which skips the sensor check when the file is opened. The data
is synthetic but physical: a phone bouncing on a spring, and a phone swinging as a pendulum.
"""

import math
import os
import random
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENTS = os.path.join(ROOT, "phyphox-experiments")

RATE = 100  #Hz
DURATION = 12  #s


def spring(t, rng):
    """Phone lying on a hand that bounces on a spring: z carries gravity plus the oscillation"""
    a = 0.0
    if t > 1.5:
        a = 4.2 * math.exp(-(t - 1.5) / 3.5) * math.sin(2 * math.pi * 1.3 * (t - 1.5))
    x = 0.12 * a + rng.gauss(0, 0.04)
    y = -0.08 * a + rng.gauss(0, 0.04)
    z = 9.81 + a + rng.gauss(0, 0.05)
    return x, y, z


def pendulum(t, rng):
    """Phone swinging on a string: the rotation is around x, slowly damped"""
    w = 0.0
    if t > 1.0:
        w = 2.6 * math.exp(-(t - 1.0) / 9) * math.sin(2 * math.pi * (t - 1.0) / 1.55)
    x = w + rng.gauss(0, 0.01)
    y = 0.04 * w + rng.gauss(0, 0.01)
    z = 0.02 * math.sin(2 * math.pi * t / 7) + rng.gauss(0, 0.01)
    return x, y, z


STATES = [
    #file, sensor, time container, x, y, z, absolute, motion
    ("accelerometer.phyphox", "accelerometer", "acc_time", "accX", "accY", "accZ", "acc", spring),
    ("gyroscope.phyphox", "gyroscope", "gyr_time", "gyrX", "gyrY", "gyrZ", "gyr", pendulum),
]


def number(v):
    return f"{v:.5g}"


def make(file, sensor, time_name, x_name, y_name, z_name, abs_name, motion, output):
    rng = random.Random(file)
    columns = {time_name: [], x_name: [], y_name: [], z_name: [], abs_name: []}
    for i in range(RATE * DURATION):
        t = i / RATE
        x, y, z = motion(t, rng)
        columns[time_name].append(t)
        columns[x_name].append(x)
        columns[y_name].append(y)
        columns[z_name].append(z)
        columns[abs_name].append(math.sqrt(x * x + y * y + z * z))

    with open(os.path.join(EXPERIMENTS, file), encoding="utf-8") as f:
        xml = f.read()
    for name, values in columns.items():
        pattern = re.compile(r'<container( [^>]*)?>' + re.escape(name) + r'</container>')
        if len(pattern.findall(xml)) != 1:
            sys.exit(f"{file}: expected one container {name}")
        init = ",".join(number(v) for v in values)
        xml = pattern.sub(lambda m: f'<container size="0" init="{init}">{name}</container>', xml)
    sensor_tag = f'<sensor type="{sensor}">'
    if xml.count(sensor_tag) != 1:
        sys.exit(f"{file}: expected one {sensor_tag}")
    xml = xml.replace(sensor_tag, f'<sensor type="{sensor}" ignoreUnavailable="true">')

    with open(os.path.join(output, file), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"{file}: {len(columns[time_name])} samples")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    output = sys.argv[1]
    os.makedirs(output, exist_ok=True)
    for state in STATES:
        make(*state, output)


if __name__ == "__main__":
    main()
