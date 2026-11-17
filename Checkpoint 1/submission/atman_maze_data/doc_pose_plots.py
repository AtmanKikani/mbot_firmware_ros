#!/usr/bin/env python3
"""Single-run (x, y) odometry plots for the checkpoint submission document."""
import csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
C = 0.61
MAZE = [(0, 0), (C, 0), (C, -C), (2*C, -C), (2*C, C), (3*C, C), (3*C, -C), (4*C, -C), (4*C, 0), (5*C, 0)]
INK, MUTED, GRID = '#1f1f1e', '#6b6a64', '#e4e3df'
RUNS = [('maze_slow_20261110_130838.csv', 'Slow run (≈0.2 m/s, π/4 rad/s)', '#2a78d6', 'doc_pose_slow.png'),
        ('maze_fast_20261110_131847.csv', 'Fast run (≈0.8 m/s, π rad/s)', '#eb6834', 'doc_pose_fast.png')]
for f, title, col, out in RUNS:
    d = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(os.path.join(HERE, f)))]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(*zip(*MAZE), color=MUTED, lw=1, ls='--', label='ideal path')
    ax.plot([r['x'] for r in d], [r['y'] for r in d], color=col, lw=2, label='odometry (x, y)')
    e = d[-1]
    ax.plot(e['x'], e['y'], 'o', ms=8, color=col, mec='white', mew=2)
    ex, ey = (0.0 if abs(v) < 5e-4 else v for v in (e['x'], e['y']))
    ax.annotate(f'end ({ex:.3f}, {ey:.3f}) m', (e['x'], e['y']), xytext=(-10, 14),
                textcoords='offset points', ha='right', fontsize=9, color=INK)
    ax.plot(0, 0, 'o', ms=6, color=MUTED); ax.annotate('start', (0, 0), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=9, color=INK)
    ax.set_title(title, loc='left', color=INK, fontsize=12, pad=8)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_aspect('equal'); ax.set_xlim(-0.2, 5*C + 0.2); ax.set_ylim(-C - 0.2, C + 0.2)
    ax.set_xlabel('x (m)', color=MUTED); ax.set_ylabel('y (m)', color=MUTED)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, out), dpi=200); plt.close(fig)
    print(out)
