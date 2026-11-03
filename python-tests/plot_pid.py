#!/usr/bin/env python3
"""Plot commanded vs. estimated MBot velocities from a pid_logger.py CSV.

Usage: python3 plot_pid.py logs/pid_log_YYYYMMDD_HHMMSS.csv
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Works through VS Code/SSH without a desktop display.
import matplotlib.pyplot as plt


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 plot_pid.py logs/pid_log_YYYYMMDD_HHMMSS.csv')
    source = Path(sys.argv[1]).expanduser()
    with source.open(newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f'CSV is empty: {source}')

    def values(column):
        return [float(row[column]) for row in rows]

    t = values('time_s')
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    plots = [
        ('cmd_vx_m_s', 'odom_vx_m_s', 'Forward velocity', 'Velocity (m/s)'),
        ('cmd_wz_rad_s', 'odom_wz_rad_s', 'Angular velocity', 'Velocity (rad/s)'),
    ]
    for ax, (cmd, actual, title, ylabel) in zip(axes, plots):
        ax.step(t, values(cmd), where='post', label='Commanded')
        ax.plot(t, values(actual), label='Estimated (odom)', alpha=0.9)
        ax.set(title=title, ylabel=ylabel)
        ax.grid(True)
        ax.legend()
    axes[-1].set_xlabel('Time since first command (s)')
    fig.tight_layout()
    dest = source.with_suffix('.png')
    fig.savefig(dest, dpi=180)
    print(f'Saved plot to {dest}')


if __name__ == '__main__':
    main()
