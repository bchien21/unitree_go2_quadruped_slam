#!/bin/bash
# Launch the Hesai XT16 ROS 2 driver standalone.
#
# Run this on the Go2's dock PC (via SSH) to publish /lidar_points over DDS.
# Then run kiss_slam.sh on the laptop/Docker container to consume the stream.
#
# The driver reads its config from:
#   go2_slam_ws/src/HesaiLidar_ROS_2.0/config/config.yaml

SETUP="source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash"

echo "Starting Hesai XT16 driver (publishing /lidar_points)..."
bash -c "$SETUP && ros2 run hesai_ros_driver hesai_ros_driver_node"
