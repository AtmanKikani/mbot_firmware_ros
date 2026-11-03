#!/usr/bin/env python3
"""Record /odom and /gyrodom into one CSV file. Stop with Ctrl+C."""
import csv
import math
from pathlib import Path
from datetime import datetime

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


def yaw_from_quaternion(q):
    """Get planar heading (radians) from ROS quaternion (x,y,z,w)."""
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class GyrodomLogger(Node):
    def __init__(self):
        super().__init__("gyrodom_logger")
        output_dir = Path(__file__).resolve().parent / "logs"
        output_dir.mkdir(exist_ok=True)
        filename = f"gyrodom_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self.output_path = output_dir / filename
        self.f = open(self.output_path, "w", newline="", buffering=1)
        self.writer = csv.writer(self.f)
        self.writer.writerow([
            "stamp_s", "topic", "x_m", "y_m", "yaw_rad", "vx_m_s", "wz_rad_s"
        ])
        self.n_odom = 0
        self.n_gyrodom = 0

        self.create_subscription(
            Odometry, "/odom", lambda msg: self.record("odom", msg), 10
        )
        self.create_subscription(
            Odometry, "/gyrodom", lambda msg: self.record("gyrodom", msg), 10
        )
        print(f"Recording /odom and /gyrodom -> {self.output_path}", flush=True)

    def record(self, topic, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.writer.writerow([
            f"{t:.9f}", topic,
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            yaw_from_quaternion(msg.pose.pose.orientation),
            msg.twist.twist.linear.x,
            msg.twist.twist.angular.z,
        ])
        if topic == "odom":
            self.n_odom += 1
        else:
            self.n_gyrodom += 1

    def close(self):
        self.f.close()
        print(f"Saved: {self.output_path}")
        print(f"Rows: odom={self.n_odom}, gyrodom={self.n_gyrodom}")


def main():
    rclpy.init()
    node = GyrodomLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
