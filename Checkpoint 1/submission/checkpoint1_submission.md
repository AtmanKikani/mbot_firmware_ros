# Checkpoint 1 Submission — Team 5

## 1. Videos

- **Slow run** (≈0.2 m/s, π/4 rad/s): https://drive.google.com/file/d/1JU_Gg3fLFLt1Is-ddUT_9om-WLHAKlTO/view?usp=sharing
- **Fast run** (≈0.8 m/s, π rad/s): https://drive.google.com/file/d/19naw11kkF5YVMuIV5jQi6KJAHm-updH4/view?usp=sharing

## 2. Odometry (x, y) plot at both speeds

Insert `atman_maze_data/maze_slow_vs_fast.png`.

*Figure: odometry (x, y) for the checkpoint path at slow (blue) and fast (orange) speed. The dashed line is the ideal path: 61 cm grid, start at (0, 0) facing +x, end at (3.05, 0).*

| Run | Time | Peak measured speeds | Final odometry pose (target 3.05, 0) |
|---|---|---|---|
| Slow (`maze_slow_20261110_130838`) | 70.3 s | 0.21 m/s, 0.89 rad/s | (3.034, −0.000) m, +0.1° |
| Fast (`maze_fast_20261110_131847`) | 34.1 s | 0.65 m/s, 3.24 rad/s | (3.087, −0.020) m, −1.0° |

- **Slow run:** tracks the path to within about 1–2 cm throughout.
- **Fast run:** finishes in half the time and ends within about 4 cm of the goal. It overshoots each corner by about 5–7 cm and curves noticeably on the two 122 cm legs. The braking limit that keeps the robot from tipping (see below) spreads each stop over time. The robot is therefore still decelerating its rotation when it starts the next straight, and the heading controller corrects that during the leg.
- **Fast-run speed:** it never reached the 0.8 m/s limit (peak 0.65 m/s). The legs are too short to accelerate to 0.8 m/s and still brake within the tipping-safe limit.

## 3. Controller description

**Firmware (low level).**
- Each wheel's speed is controlled by a PD loop at 100 Hz, using encoder feedback (gains tuned in Task 1.2).
- Odometry is computed on the Pico from the encoders and published on `/odom`.
- During this checkpoint we found and fixed two odometry errors:
  1. **Loop timing bug (about 6% under-count).** The control-loop timer was set up so that each callback's own run time was added to the 10 ms period, giving an actual period of 10.6 ms. Pose was still integrated as velocity × 10 ms, so every update was about 6% short. The timer now runs on a fixed 10 ms schedule, and odometry uses the measured time step.
  2. **Wheel and base radius calibration (about 2.5% over-count).** We calibrated the radii from a 2 m tape-measured straight drive and a 5-turn spin on a yaw poster: wheel radius 0.04183 → 0.04172 m, base radius 0.085 → 0.08695 m.
- **Effect:** after both fixes, odometry yaw error over 3 full turns dropped from 38° to 2.2° RMS. A 4-loop 1 m square ends within 4–5 cm and about 7° of the start.
- **Gyrodometry:** we also implemented gyrodometry (heading from the IMU gyro), published on `/gyrodom`. Wheel odometry was more accurate in our benchmark (2.2° vs 4.6° RMS over 3 turns), so `/odom` remains wheel-based.

**Motion controller (high level): Rotate-Translate-Rotate (RTR).** It runs at 20 Hz in `controller_node`, takes a list of waypoints (x, y, θ), and publishes `/cmd_vel`. It is an explicit state machine:
1. **Rotate to target:** a PID on the bearing error turns the robot in place to face the next waypoint, until the error is under 1.1°.
2. **Translate:** a PID on the remaining distance, measured along the robot's heading, sets the forward speed, so an overshoot ends the leg instead of making the robot reverse. A heading PID steers toward the waypoint; steering is switched off in the last 10 cm, where the bearing becomes noisy. If the heading error goes above 20°, the controller falls back to rotating in place.
3. **Rotate to final heading:** turns to the waypoint's θ, then loads the next waypoint. Each waypoint's θ is set to the direction the robot arrives from, so it never makes a needless turn at a corner.

**Features to be aware of:**
- **Explicit states:** the template re-chooses the phase from thresholds every tick, which lets odometry noise near a waypoint flip the robot between phases. The state machine prevents that.
- **Acceleration *and* braking limits, plus a stopping-distance speed cap:**
  - Commanded speed is capped at v ≤ √(2·a_brake·d), where d is the remaining distance, so the robot always starts braking early enough to stop on the waypoint. Turning uses the same rule.
  - Without a braking limit, our first fast attempt tipped the robot over when it stopped hard from about 0.8 m/s.
- **Minimum speeds** (0.04 m/s, 0.15 rad/s): stop the robot stalling short of a target because of motor deadband.
- **No derivative kick:** the stored PID error is re-seeded each time the phase changes.
- **Arrival tolerances:** 2 cm and 1.1°.
- **Runtime parameters, no rebuild needed:** speed limits, gains and acceleration/braking limits can all be set at launch.

  | Setting | Slow run | Fast run |
  |---|---|---|
  | Max linear speed | 0.2 m/s | 0.8 m/s |
  | Max angular speed | 0.785 rad/s | 3.14 rad/s |
  | Kp linear / angular | 1.0 / 2.0 (defaults) | 2.5 / 4.0 |
  | Acceleration / braking, linear | 0.6 / 0.6 m/s² (defaults) | 1.2 / 1.0 m/s² |
  | Acceleration / braking, angular | 3 / 3 rad/s² (defaults) | 10 / 6 rad/s² |
