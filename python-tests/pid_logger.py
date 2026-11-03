#!/usr/bin/env python3
"""Record MBot commanded and encoder-estimated velocities for PID tuning.

Run this before python3 step_cmd_test.py, then stop it with Ctrl+C.
CSV output is written next to this script in a logs/ directory.
"""
import csv
import time
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class PIDLogger(Node):
    def __init__(self):
        super().__init__('pid_logger')

        output_dir = Path(__file__).resolve().parent / 'logs'
        output_dir.mkdir(exist_ok=True)
        filename = f"pid_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self.output_path = output_dir / filename
        self.output_file = self.output_path.open('w', newline='', buffering=1)
        self.writer = csv.writer(self.output_file)
        self.writer.writerow(['time_s', 'cmd_vx_m_s', 'odom_vx_m_s',
                              'cmd_wz_rad_s', 'odom_wz_rad_s'])

        self.start_time = None
        self.latest_cmd = None
        self.num_rows = 0

        self.create_subscription(Twist, '/cmd_vel', self.on_cmd_vel, 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.get_logger().info(f"Recording to {self.output_path}")
        self.get_logger().info('Start step_cmd_test.py in another terminal. Press Ctrl+C here to stop.')

    def on_cmd_vel(self, msg):
        if self.start_time is None:
            self.start_time = time.monotonic()
        self.latest_cmd = (msg.linear.x, msg.angular.z)

    def on_odom(self, msg):
        if self.latest_cmd is None:
            return  # Ignore odometry until the first command arrives.
        t = time.monotonic() - self.start_time
        cmd_vx, cmd_wz = self.latest_cmd
        self.writer.writerow([f'{t:.4f}', f'{cmd_vx:.6f}',
                              f'{msg.twist.twist.linear.x:.6f}',
                              f'{cmd_wz:.6f}',
                              f'{msg.twist.twist.angular.z:.6f}'])
        self.num_rows += 1

    def close(self):
        self.output_file.close()
        self.get_logger().info(f'Saved {self.num_rows} rows to {self.output_path}')


def main():
    rclpy.init()
    node = PIDLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
