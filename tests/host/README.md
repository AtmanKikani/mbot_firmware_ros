# Host test for wheel_pid

Runs on the Pi or any Linux machine with `gcc`. It isn't built for the Pico.

```bash
tests/host/build_host_test.sh
```

It checks that `wheel_pid` matches `rc_filter_pid` to float precision when nothing saturates, then
prints both controllers on two saturating sequences. Expected output:

- Unsaturated equivalence: worst relative difference at most 1e-5.
- PI step: RCLib falls away from 1 (`1, 1, 1, 0.804, 0.716, 0.322, 0.227, -0.072, ...`); `wheel_pid` stays at 1.
- PID with constant e = 10: RCLib goes to -1 (`1, -0.8, -1, -1, ...`); `wheel_pid` stays at 1.
