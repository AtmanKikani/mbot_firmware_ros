"""Log /cmd_vel and /odom to a CSV file, using one clock for both topics.

Usage:
    python3 log_step.py mode0_run1.csv
Stop with Ctrl+C. The CSV is written when you stop.
"""
import csv
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy


class StepLogger(Node):
    def __init__(self):
        super().__init__("step_logger")
        # BEST_EFFORT can receive from both reliable and best effort publishers.
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=100)
        self.rows = []
        self.t0 = time.time()  # time zero = when logging starts
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, qos)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos)

    def on_cmd(self, msg):
        t = time.time() - self.t0  # time this computer received the message
        self.rows.append([t, "cmd", msg.linear.x, msg.angular.z])

    def on_odom(self, msg):
        t = time.time() - self.t0
        twist = msg.twist.twist
        self.rows.append([t, "odom", twist.linear.x, twist.angular.z])

    def save(self, filename):
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t", "topic", "linear_x", "angular_z"])
            writer.writerows(self.rows)
        print(f"Saved {len(self.rows)} rows to {filename}")


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "step_log.csv"
    rclpy.init()
    node = StepLogger()
    print("Logging... press Ctrl+C to stop and save.")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.save(filename)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
