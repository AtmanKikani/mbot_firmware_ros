# Checkpoint 1 — Tasks 1.3 & 1.4

Team 5. All runs on 2026-11-10.

## Task 1.3 — Improve firmware (gyrodometry)

### Implementation
- **`src/mbot_odometry.c`**: added `mbot_calculate_gyrodometry()`. It updates x and y from the encoder forward speed, like wheel odometry, but integrates heading from the IMU gyro z rate instead of the encoder-derived `wz`.
- **`src/mbot_classic_ros.h`**: added a separate gyrodometry pose to `mbot_state_t` (`gyrodom_x`, `gyrodom_y`, `gyrodom_theta`), so both estimators run side by side.
- **`src/mbot_ros_comms.c/.h`**:
  - Added a new `nav_msgs/Odometry` publisher on **`/gyrodom`** (frames `odom` → `base_footprint`).
  - `/reset_odometry` now resets both poses.
- **`src/mbot_classic_ros.c`**:
  - Both estimators are computed every control tick.
  - `/gyrodom` is published at 25 Hz alongside `/odom`, with the same timestamp. Its twist carries the gyro `wz`.

### Benchmark
- **Script:** `mbot_ros_labs/src/scripts/yaw_benchmark.py`
- **Ground truth:** a yaw poster on the floor with ±15/30/45° marks.
- **Sequence:**
  - Slow steps at 0.3 rad/s to +15, +30, +45, 0, −15, −30, −45, 0.
  - 3 full turns counter-clockwise at about 1 rad/s, then 3 turns clockwise back.
- **Data and plots:** `Checkpoint 1/1.3/atman_benchmark_data/`
  - Plots: `step_error.png`, `estimate_vs_truth.png`, `spin_error.png`
  - Tables: `summary.txt`, `yaw_benchmark_corrected.csv`

The benchmark was run twice: before and after the firmware fixes found in Task 1.4 (loop timing and radius calibration).

| | Before fixes: /odom | Before fixes: /gyrodom | **After fixes: /odom** | **After fixes: /gyrodom** |
|---|---|---|---|---|
| Slow ±15/30/45° steps (RMS) | 1.06° | 1.25° | **0.96°** | **1.48°** |
| 3-turn spins (RMS) | 38.39° | 60.20° | **2.19°** | **4.58°** |

- **Before** (`yaw_benchmark_20261110_113741_raw.csv`, results in `atman_benchmark_data/`):
  - The turns were steered by `/gyrodom`.
  - Both estimators under-counted fast rotation (+3 turns: odom −54°, gyrodom −85°) because of the loop-timing bug described in Task 1.4.
  - The perfect return to 0 after the CW leg was only cancellation: the CW leg under-counted by the same amount.
- **After** (`post_timing_fix/yaw_benchmark_20261110_124142.csv`, results in `post_timing_fix/`):
  - The turns were steered by `/odom`.
  - Spin error dropped about 18× for odom and about 13× for gyrodom.
  - The ground-truth entry for the −30° step was typed without its sign; `analyze_yaw_benchmark.py` corrects this automatically.
- **Comparison plots** (made by `compare_before_after.py`):
  - `before_after_rms.png`: RMS error per estimator, before vs after.
  - `before_after_spin.png`: per-stop spin errors.
  - `before_after_summary.txt`: the same numbers as text.

**Decision:** keep wheel odometry on `/odom`. After the fixes it beats gyrodometry on both the slow steps and the fast spins. Gyrodom's small, consistent under-read (−5° over 1080°, about 0.5%) points to a slight gyro scale error. `/gyrodom` still publishes for comparison.

## Task 1.4 — Motion controller (RTR)

### Controller (`mbot_nav/src/controllers/rtr_controller.cpp/.hpp`)
Rotate-Translate-Rotate, built as an explicit state machine and run at 20 Hz:

1. **ROTATE_TO_TARGET:** a PID on the bearing error turns the robot in place to face the waypoint. It switches to TRANSLATE once the error is under `angle_thresh_`.
2. **TRANSLATE:**
   - A PID on the distance-to-go, *measured along the current heading*, sets the forward speed. If the robot overshoots, it moves on instead of reversing.
   - A heading PID steers toward the waypoint. Steering is disabled in the last 10 cm, where the bearing becomes noisy.
   - If the heading error grows past 0.35 rad, the controller falls back to ROTATE_TO_TARGET.
3. **ROTATE_TO_FINAL:** rotates to the waypoint's θ, then loads the next waypoint.

Why an explicit state machine: the template re-picks the phase from thresholds every tick. With that, small odometry noise near a waypoint can bounce the robot between phases.

**Other features:**
- **Thresholds:** 2 cm on distance, 0.02 rad (1.1°) on angle.
- **Minimum speeds:** 0.04 m/s and 0.15 rad/s, so the robot doesn't stall just short of a target.
- **Acceleration limits:** 0.6 m/s² and 3 rad/s², applied only when speeding up. They reduce wheel slip, which keeps odometry accurate.
- **No derivative kick:** the stored PID error is re-seeded after each phase change.
- **Gains:**

  | | Kp | Ki | Kd |
  |---|---|---|---|
  | Linear | 1.0 | 0 | 0.01 |
  | Angular | 2.0 | 0 | 0.05 |

- **Speed limits:** `controller_node` parameters `max_linear_vel` (default 0.3 m/s) and `max_angular_vel` (default 1.0 rad/s).
- **`square_publisher`:** parameters `loops` (default 1) and `side` (default 1.0 m).

### Firmware issues found during the square test

**1. Control-loop timing bug (odometry under-counted by about 6%).**
- *Symptom:* after 4 loops, odom reported a near-perfect return to start. In reality the robot overshot every side and corner, ending about 90° rotated and about one side ahead.
- *Cause:*
  - Wheel velocity is computed with the measured `encoder_delta_t`, but pose was integrated as `velocity × MAIN_LOOP_PERIOD` (the nominal 10 ms).
  - The loop timer used `add_repeating_timer_ms(+10)`. In the Pico SDK, a positive delay is measured from the *end* of one callback to the *start* of the next, so the callback's own run time was added to every period.
  - `/encoders` showed `delta_time = 10623 µs`, so each update under-counted by about 6%.
  - The recorded data confirms it: integrating the reported twist gave 1547° and 16.5 m, while the pose showed only 1438° and 15.3 m.
- *Fix (`src/mbot_classic_ros.c`):*
  - The timer delay is now negative, which gives a fixed 10 ms start-to-start period. `delta_time` now reads 10001 µs.
  - Odometry and gyrodometry now integrate with the measured `encoder_delta_t` instead of the nominal period.

**2. Kinematic calibration (odometry over-counted by about 2.5% after fix 1).**
- *Symptom:* the robot now fell short on turns and straights, ending about −30° and about 40 cm off after 4 loops.
- *Procedure:* `mbot_ros_labs/src/scripts/odom_calibration.py`
  - Drive 2.000 m by odometry and tape-measure the real distance: 1.995 m, so the distance scale is s = 0.9973.
  - Spin 5 turns at 1 rad/s by odometry and read the poster: the real rotation was 1755° for 1800.3° on odom, so the rotation scale is k = 0.9749.
  - Since rotation ∝ r/B: r_new = r·s and B_new = B·s/k.
- *Result (`include/config/mbot_classic_config.h`):*

  | Constant | Old | New |
  |---|---|---|
  | `DIFF_WHEEL_RADIUS` | 0.04183 | 0.04172 |
  | `DIFF_BASE_RADIUS` | 0.085 | 0.08695 |

### Square test results (1 m square, 4 loops, 0.3 m/s / 1.0 rad/s)

| Run | Firmware state | Final error vs. start (measured on floor) |
|---|---|---|
| `square_20261110_115510` | Original (timing bug), first attempt | — |
| `square_20261110_115736` | Original (timing bug) | about +90° heading, about 1 side ahead (overshoot) |
| `square_20261110_120930` | Timing fixed, original radii | about −30° heading, about 40 cm short (undershoot) |
| `square_20261110_122530` | Timing fixed + calibrated radii | — (recorder stopped early on encoder noise, no motion captured; the recorder was fixed afterwards) |
| **`square_20261110_123745`** | **Timing fixed + calibrated radii** | **about +7° heading, 4–5 cm (3–4 cm right and 3–4 cm forward)** |

All runs are kept in `1.4/atman_square_data/` as the development record.

- **Script:** `mbot_ros_labs/src/scripts/square_benchmark.py`. It records `/odom` and `/cmd_vel`, then writes `*_pose.png` (estimated (x, y) over all loops) and `*_velocity.png` (commanded vs measured vx and wz for loop 1).
- **Output folder:** `Checkpoint 1/1.4/atman_square_data/`.
- **Final run: `square_20261110_123745`** (timing fixed + calibrated radii)
  - `square_20261110_123745_pose.png`: estimated (x, y) over 4 loops.
    - The loops overlap closely.
    - Odometry's final pose is (+0.002, +0.016) m and −0.3°.
    - The real final error measured on the floor is 4–5 cm and about +7°. The difference is drift that odometry cannot see: slip, and leftover calibration error.
  - `square_20261110_123745_velocity.png`: commanded vs measured vx and wz for loop 1 (about 29 s).
    - Measured velocity tracks the command closely: 0.3 m/s cruise with a ramp up, a P-controlled slowdown to the 0.04 m/s minimum, and 1.0 rad/s turns.
    - The ±0.05–0.1 rad/s ripple on wz is encoder quantization at 100 Hz.

### How to reproduce
```bash
# firmware
cd ~/mbot_firmware_ros/build && cmake .. && make && sudo mbot-upload-firmware flash mbot_classic_ros.uf2

# controller (each terminal: cd ~/mbot_ros_labs && source install/setup.bash)
colcon build --packages-select mbot_nav
python3 ~/mbot_ros_labs/src/scripts/square_benchmark.py            # T1: resets odom, records, plots
ros2 run mbot_nav controller_node                              # T2 (add -p max_linear_vel:=… -p max_angular_vel:=…)
ros2 run mbot_nav square_publisher --ros-args -p loops:=4      # T3
```
