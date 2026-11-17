#!/usr/bin/env python3
"""Before/after the control-loop timing fix: yaw RMS error of /odom and /gyrodom."""
import csv, math, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = os.path.join(HERE, 'yaw_benchmark_corrected.csv')                    # run 2026-11-10 11:37, gyrodom feedback
AFTER = os.path.join(HERE, 'post_timing_fix', 'yaw_benchmark_corrected.csv')  # run 2026-11-10 12:41, odom feedback
INK, MUTED, GRID = '#1f1f1e', '#6b6a64', '#e4e3df'
COL = {('odom', 'before'): '#86b6ef', ('odom', 'after'): '#2a78d6',
       ('gyrodom', 'before'): '#f4a882', ('gyrodom', 'after'): '#eb6834'}

def load(p):
    return [{k: (v if k == 'step' else float(v)) for k, v in r.items()} for r in csv.DictReader(open(p))]

def rms(rows, k):
    return math.sqrt(sum(r[k] ** 2 for r in rows) / len(rows))

runs = {'before': load(BEFORE), 'after': load(AFTER)}
groups = {'Slow ±15/30/45° steps': lambda r: r['step'].startswith('step'),
          '3-turn spins (≈1 rad/s)': lambda r: r['step'].startswith('spin')}

fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
lines = []
for ax, (title, sel) in zip(axes, groups.items()):
    bars = []
    for est in ('odom', 'gyrodom'):
        for when in ('before', 'after'):
            bars.append((est, when, rms([r for r in runs[when] if sel(r)], f'{est}_err')))
    xs = [0, 0.9, 2.3, 3.2]
    for x, (est, when, v) in zip(xs, bars):
        ax.bar(x, v, width=0.85, color=COL[(est, when)], edgecolor='white', linewidth=2,
               label=f'/{est} {when} fixes')
        ax.annotate(f'{v:.2f}°', (x, v), xytext=(0, 4), textcoords='offset points',
                    ha='center', fontsize=9, color=INK)
    ax.set_xticks([0.45, 2.75]); ax.set_xticklabels(['/odom', '/gyrodom'])
    ax.set_title(title, loc='left', color=INK, fontsize=11, pad=8)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_ylabel('RMS yaw error (deg)', color=MUTED)
    lo, hi = ax.get_ylim(); ax.set_ylim(0, hi * 1.12)
    lines.append((title, bars))

h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=9, labelcolor=INK, loc='lower center', ncol=4)
fig.suptitle('Yaw error before vs after firmware fixes (loop timing + wheel/base radius calibration)', x=0.01, ha='left', color=INK, fontsize=12)
fig.tight_layout(rect=(0, 0.07, 1, 0.96))
fig.savefig(os.path.join(HERE, 'before_after_rms.png'), dpi=150); plt.close(fig)

# Per-stop spin errors, before vs after
fig, ax = plt.subplots(figsize=(8, 4.8))
labels = ['+3 turns CCW', '−3 turns CW (back to 0)']
spins = {w: [r for r in runs[w] if r['step'].startswith('spin')] for w in runs}
offs = {('odom', 'before'): -0.3, ('odom', 'after'): -0.1, ('gyrodom', 'before'): 0.1, ('gyrodom', 'after'): 0.3}
for (est, when), dx in offs.items():
    vals = [r[f'{est}_err'] for r in spins[when]]
    xs = [i + dx for i in range(len(vals))]
    ax.bar(xs, vals, width=0.19, color=COL[(est, when)], edgecolor='white', linewidth=1.5, label=f'/{est} {when} fixes')
    for x, v in zip(xs, vals):
        ax.annotate(f'{v:+.1f}°', (x, v), xytext=(0, -11 if v < 0 else 3), textcoords='offset points',
                    ha='center', fontsize=8, color=INK)
ax.axhline(0, color=MUTED, lw=1)
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels)
ax.set_title('Yaw error after 3-turn spins, before vs after firmware fixes', loc='left', color=INK, fontsize=11, pad=8)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED, labelsize=9); ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_ylabel('estimate − ground truth (deg)', color=MUTED)
lo, hi = ax.get_ylim(); ax.set_ylim(lo - 0.1 * (hi - lo), hi + 0.1 * (hi - lo))
ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'before_after_spin.png'), dpi=150); plt.close(fig)

out = ['Yaw RMS error (deg), before -> after firmware fixes (timing + radius calibration)']
for title, bars in lines:
    d = {(e, w): v for e, w, v in bars}
    for e in ('odom', 'gyrodom'):
        b, a = d[(e, 'before')], d[(e, 'after')]
        out.append(f'  {title:<26} /{e:<8} {b:6.2f} -> {a:5.2f}  ({b / a:.1f}x lower)')
open(os.path.join(HERE, 'before_after_summary.txt'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
