#!/usr/bin/env python3
"""Bridge Unitree /utlidar/robot_odom Odometry -> TF (odom -> base_link).

Unitree's native Go2 daemon publishes an Odometry message on
/utlidar/robot_odom at ~150 Hz but does NOT emit a matching /tf transform.
RTAB-Map, Nav2 and RViz all expect the odom->base_link edge of the TF tree
to exist, so we republish the pose here.

Run on the Jetson (or wherever the Unitree daemon's DDS traffic is visible).
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomToTf(Node):
    def __init__(self) -> None:
        super().__init__('unitree_odom_to_tf')
        self.declare_parameter('odom_topic', '/utlidar/robot_odom')
        self.declare_parameter('parent_frame', 'odom')
        self.declare_parameter('child_frame', 'base_link')
        self.declare_parameter('publish_rate_hz', 50.0)

        topic = self.get_parameter('odom_topic').value
        self._parent = self.get_parameter('parent_frame').value
        self._child = self.get_parameter('child_frame').value
        rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self._min_period_ns = int(1e9 / rate_hz) if rate_hz > 0 else 0
        self._last_pub_ns = 0

        self._br = TransformBroadcaster(self)
        self._sub = self.create_subscription(Odometry, topic, self._cb, 50)
        self.get_logger().info(
            f'Republishing {topic} as TF {self._parent} -> {self._child} '
            f'at up to {rate_hz:.1f} Hz'
        )

    def _cb(self, msg: Odometry) -> None:
        now_ns = self.get_clock().now().nanoseconds
        if self._min_period_ns and now_ns - self._last_pub_ns < self._min_period_ns:
            return
        self._last_pub_ns = now_ns

        t = TransformStamped()
        t.header = msg.header
        t.header.frame_id = self._parent
        t.child_frame_id = self._child
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self._br.sendTransform(t)


def main() -> None:
    rclpy.init()
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
