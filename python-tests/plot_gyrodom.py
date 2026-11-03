#!/usr/bin/env python3
"""Plot the logger CSV. Optionally overlay a physically measured final pose."""
import argparse
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Save a PNG even without a graphical desktop
import matplotlib.pyplot as plt
import numpy as np


parser = argparse.ArgumentParser(description="Compare /odom and /gyrodom")
parser.add_argument("csv_file", help="CSV created by log_gyrodom.py")
parser.add_argument("--true-x", type=float, help="Measured final X (meters)")
parser.add_argument("--true-y", type=float, help="Measured final Y (meters)")
parser.add_argument("--true-yaw-deg", type=float, help="Measured final heading (degrees)")
args = parser.parse_args()

path = Path(args.csv_file)
rows = {"odom": [], "gyrodom": []}
with path.open(newline="") as file:
    for row in csv.DictReader(file):
        if row["topic"] in rows:
            rows[row["topic"]].append(row)

if not rows["odom"] or not rows["gyrodom"]:
    raise SystemExit("CSV must contain measurements from BOTH /odom and /gyrodom.")

t0 = min(float(r["stamp_s"]) for dataset in rows.values() for r in dataset)
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

for topic, dataset in rows.items():
    dataset.sort(key=lambda r: float(r["stamp_s"]))
    t = np.array([float(r["stamp_s"]) - t0 for r in dataset])
    x = np.array([float(r["x_m"]) for r in dataset])
    y = np.array([float(r["y_m"]) for r in dataset])
    yaw = np.unwrap(np.array([float(r["yaw_rad"]) for r in dataset]))
    label = "Wheel odometry (/odom)" if topic == "odom" else "Gyrodometry (/gyrodom)"

    axes[0, 0].plot(x, y, label=label)
    axes[0, 1].plot(t, np.rad2deg(yaw), label=label)
    axes[1, 0].plot(t, x, label=label)
    axes[1, 1].plot(t, y, label=label)

    print(f"{topic}: final X={x[-1]:.3f} m, Y={y[-1]:.3f} m, "
          f"heading={np.rad2deg(yaw[-1]):.1f} deg")
    if args.true_x is not None and args.true_y is not None:
        error = math.hypot(x[-1] - args.true_x, y[-1] - args.true_y)
        print(f"    Final position error = {error:.3f} m")
    if args.true_yaw_deg is not None:
        err_rad = math.atan2(math.sin(yaw[-1] - math.radians(args.true_yaw_deg)),
                             math.cos(yaw[-1] - math.radians(args.true_yaw_deg)))
        print(f"    Final heading error = {abs(math.degrees(err_rad)):.1f} deg")

if args.true_x is not None and args.true_y is not None:
    axes[0, 0].scatter([args.true_x], [args.true_y], marker="x", s=110,
                       label="Measured final position")
if args.true_yaw_deg is not None:
    last_t = max(float(r["stamp_s"]) - t0 for dataset in rows.values() for r in dataset)
    axes[0, 1].scatter([last_t], [args.true_yaw_deg], marker="x", s=110,
                       label="Measured final heading")

axes[0, 0].set(title="XY path", xlabel="X (m)", ylabel="Y (m)")
axes[0, 0].set_aspect("equal", adjustable="datalim")
axes[0, 1].set(title="Heading vs time", xlabel="Time (s)", ylabel="Yaw (degrees)")
axes[1, 0].set(title="X vs time", xlabel="Time (s)", ylabel="X (m)")
axes[1, 1].set(title="Y vs time", xlabel="Time (s)", ylabel="Y (m)")
for ax in axes.flat:
    ax.grid(True)
    ax.legend(fontsize=8)
fig.tight_layout()
png_path = path.with_suffix(".png")
fig.savefig(png_path, dpi=180)
print(f"\nPlot saved to: {png_path}")
