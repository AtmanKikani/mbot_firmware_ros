#!/usr/bin/env python3
"""Corrects sign of ground truth on negative steps and plots /odom vs /gyrodom yaw error."""
import csv, math, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, 'yaw_benchmark_20261110_113741_raw.csv')
# Outputs go next to the input CSV, so separate runs never overwrite each other
HERE = os.path.dirname(os.path.abspath(RAW))
ODOM_C, GYRO_C = '#2a78d6', '#eb6834'
INK, MUTED, GRID = '#1f1f1e', '#6b6a64', '#e4e3df'

rows = list(csv.DictReader(open(RAW)))
for r in rows:
    for k in ('target_deg', 'gt_deg', 'odom_deg', 'gyrodom_deg'):
        r[k] = float(r[k])
    # Ground truth was entered without a sign on negative targets
    if r['target_deg'] < 0 and r['gt_deg'] > 0:
        r['gt_deg'] = -r['gt_deg']
    r['odom_err'] = r['odom_deg'] - r['gt_deg']
    r['gyrodom_err'] = r['gyrodom_deg'] - r['gt_deg']

out_csv = os.path.join(HERE, 'yaw_benchmark_corrected.csv')
with open(out_csv, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

steps = [r for r in rows if r['step'].startswith('step')]
spins = [r for r in rows if r['step'].startswith('spin')]
rms = lambda rs, k: math.sqrt(sum(r[k] ** 2 for r in rs) / len(rs))

def style(ax, title):
    ax.set_title(title, loc='left', color=INK, fontsize=12, pad=10)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.axhline(0, color=MUTED, lw=1)

def grouped(ax, rs, labels):
    x = range(len(rs)); bw = 0.38
    for i, (k, c, name) in enumerate([('odom_err', ODOM_C, '/odom'), ('gyrodom_err', GYRO_C, '/gyrodom')]):
        xs = [xi + (i - 0.5) * (bw + 0.02) for xi in x]
        vals = [r[k] for r in rs]
        ax.bar(xs, vals, width=bw, color=c, label=f'{name} (RMS {rms(rs, k):.2f}°)', edgecolor='white', linewidth=1)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel('estimate − ground truth (deg)', color=MUTED)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=2)
    lo, hi = ax.get_ylim(); pad = 0.12 * (hi - lo); ax.set_ylim(lo - pad, hi + pad)

# Fig 1: small-step errors
fig, ax = plt.subplots(figsize=(9, 5))
style(ax, 'Yaw error at slow ±15/30/45° steps (in sequence order)')
grouped(ax, steps, [f'{int(r["target_deg"]):+d}°' for r in steps])
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'step_error.png'), dpi=150); plt.close(fig)

# Fig 2: estimate vs ground truth (small steps)
fig, ax = plt.subplots(figsize=(5.5, 5.5))
style(ax, 'Estimated vs ground-truth yaw (steps)')
lim = [-55, 55]
ax.plot(lim, lim, color=MUTED, lw=1, ls='--', label='ideal')
ax.scatter([r['gt_deg'] for r in steps], [r['odom_deg'] for r in steps], s=55, color=ODOM_C, edgecolor='white', lw=2, label='/odom', zorder=3)
ax.scatter([r['gt_deg'] for r in steps], [r['gyrodom_deg'] for r in steps], s=55, color=GYRO_C, edgecolor='white', lw=2, marker='s', label='/gyrodom', zorder=3)
ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect('equal')
ax.set_xlabel('ground truth (deg)', color=MUTED); ax.set_ylabel('estimate (deg)', color=MUTED)
ax.legend(frameon=False, fontsize=9, labelcolor=INK)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'estimate_vs_truth.png'), dpi=150); plt.close(fig)

# Fig 3: multi-turn spin errors
fig, ax = plt.subplots(figsize=(6.5, 5))
style(ax, 'Yaw error after 3-turn spins (≈1 rad/s)')
grouped(ax, spins, ['+3 turns CCW', '−3 turns CW (back to 0)'])
for r_i, r in enumerate(spins):
    for i, k in enumerate(('odom_err', 'gyrodom_err')):
        v = r[k]; ax.annotate(f'{v:+.1f}°', (r_i + (i - 0.5) * 0.4, v), ha='center',
                              va='top' if v < 0 else 'bottom', xytext=(0, -4 if v < 0 else 4),
                              textcoords='offset points', fontsize=9, color=INK)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'spin_error.png'), dpi=150); plt.close(fig)

# Summary
hdr = f'{"step":<26}{"GT":>9}{"odom":>10}{"gyrodom":>10}{"odom err":>10}{"gyro err":>10}'
lines = [hdr] + [f'{r["step"]:<26}{r["gt_deg"]:>9.2f}{r["odom_deg"]:>10.2f}{r["gyrodom_deg"]:>10.2f}{r["odom_err"]:>10.2f}{r["gyrodom_err"]:>10.2f}' for r in rows]
lines += ['', f'RMS (steps)  odom {rms(steps,"odom_err"):.2f}  gyrodom {rms(steps,"gyrodom_err"):.2f} deg',
          f'RMS (spins)  odom {rms(spins,"odom_err"):.2f}  gyrodom {rms(spins,"gyrodom_err"):.2f} deg',
          f'RMS (all)    odom {rms(rows,"odom_err"):.2f}  gyrodom {rms(rows,"gyrodom_err"):.2f} deg']
open(os.path.join(HERE, 'summary.txt'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
