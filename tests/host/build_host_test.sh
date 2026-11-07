#!/usr/bin/env bash
# Host check (no Pico needed): wheel_pid must equal rc_filter_pid when nothing saturates,
# and must not lose proportional action when it does.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
FW=$(cd "$HERE/../.." && pwd)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
gcc -std=gnu11 -O0 -Wall -I"$FW/rc/include" -I"$FW/src" \
    "$HERE/test_wheel_pid_vs_rclib.c" "$FW/src/wheel_pid.c" "$FW"/rc/src/math/*.c -lm -o "$OUT/test_wheel_pid"
"$OUT/test_wheel_pid"
