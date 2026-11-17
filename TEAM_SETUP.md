# MBot setup checklist: get your robot onto the fixed firmware

About 20 minutes per robot. This brings your MBot up to date with the Checkpoint 1 fixes. Do the steps in order.

**Why bother:**
- The old firmware under-counted every motion by about 6% because of a loop-timing bug, so the robot overshoots everything.
- The wheel and base radii also have to be calibrated **for your own robot**. The values in `main` are Atman's.

**You need:**
- A tape measure.
- 2 m of clear straight floor.
- The yaw poster (±15/30/45° marks).
- Task 1.1 motor calibration and your wheel PID gains already done. Those live on the board and are not touched by these steps.

---

## ☐ 1. Pull the latest code (both repos)
```bash
cd ~/mbot_firmware_ros && git checkout main && git pull
cd ~/mbot_ros_labs/src  && git checkout main && git pull
```
Got local changes? Run `git stash` first, or commit them to your own branch.

## ☐ 2. Build and flash the firmware
```bash
cd ~/mbot_firmware_ros/build && cmake .. && make && sudo mbot-upload-firmware flash mbot_classic_ros.uf2
```
**Check the timing fix worked:**
```bash
ros2 topic echo --once /encoders     # delta_time should be ~10000 (it was ~10600 before the fix)
```

## ☐ 3. Build the nav package
```bash
cd ~/mbot_ros_labs && colcon build --packages-select mbot_nav && source install/setup.bash
```
Re-run `source ~/mbot_ros_labs/install/setup.bash` in **every** new terminal.

## ☐ 4. Calibrate your robot's wheel and base radius
Do this only *after* step 2. The script reads the radii from the config file, so the robot must be running firmware built from that same file.
```bash
python3 ~/mbot_ros_labs/src/scripts/odom_calibration.py --dist 2.0 --turns 4
```
1. **Straight:** mark where the robot starts (for example, the front axle on a tape line) and press Enter. It drives 2 m. At `RECORD NOW`, type the **measured distance in metres** (for example `1.995`).
2. **Spin:** put the robot on the poster's 0 mark and press Enter. It spins 4 turns counter-clockwise. At `RECORD NOW`, type the **signed poster reading**: counter-clockwise is positive, so short of 0 is negative, for example `-12`.
   - If the reading is past ±45°, rerun with `--turns 2`.

It prints two lines, for example:
```
#define DIFF_WHEEL_RADIUS            0.04172
#define DIFF_BASE_RADIUS             0.08695
```

## ☐ 5. Put your values in and reflash
1. Edit lines 10–11 of `~/mbot_firmware_ros/include/config/mbot_classic_config.h` with **your** two values.
2. Rebuild and flash:
   ```bash
   cd ~/mbot_firmware_ros/build && make && sudo mbot-upload-firmware flash mbot_classic_ros.uf2
   ```

⚠️ **Don't push your radii to `main`.** They only fit your robot. Keep them in your local copy or on your own branch.

## ☐ 6. Verify with the square test (4 loops of a 1 m square)
Use three terminals, each sourced as in step 3. Put the robot on a marked start, facing +x.
```bash
python3 ~/mbot_ros_labs/src/scripts/square_benchmark.py          # T1: resets odom, records, plots
ros2 run mbot_nav controller_node                                  # T2
ros2 run mbot_nav square_publisher --ros-args -p loops:=4          # T3
```
**Pass:** the robot ends within **about 5 cm and about 10°** of where it started.
- **Consistently over-turning or under-turning:** redo step 4 (more turns gives more accuracy, but stay within the poster's ±45°).
- **Overshooting or undershooting on everything:** step 2 didn't flash. Check `delta_time` again.

Plots are saved to `~/mbot_firmware_ros/Checkpoint 1/1.4/atman_square_data/`.

---

## Good to know
- **Restart both `controller_node` and the waypoint publisher for every run.** The controller reads its settings at startup, and the publisher only sends the path once. The recorder script resets odometry for you.
- **Checkpoint path:** `ros2 run mbot_nav maze_publisher` drives the checkpoint path. Start the robot on Start, facing End.
- **Speed settings:**

  | Run | Add to `controller_node` |
  |---|---|
  | Slow | `--ros-args -p max_linear_vel:=0.2 -p max_angular_vel:=0.785` |
  | Fast | `--ros-args -p max_linear_vel:=0.8 -p max_angular_vel:=3.14 -p kp_linear:=2.5 -p kp_angular:=4.0 -p max_linear_accel:=1.2 -p max_linear_decel:=1.0 -p max_angular_accel:=10.0 -p max_angular_decel:=6.0` |

  Don't raise the braking limits above these values: hard stops at 0.8 m/s tip the robot over.
- **Full details:** what was wrong and the before/after numbers are in `Checkpoint 1/README.md`.
