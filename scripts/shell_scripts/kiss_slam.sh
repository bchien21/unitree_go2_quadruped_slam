#!/bin/bash
# Launch KISS-SLAM (odometry + loop closure + occupancy grid) + RViz.
#
# Run this on the laptop / Docker container.
# Assumes /lidar_points is already being published (run hesai_driver.sh on
# the dock PC first).
#
# Pane layout (tiled):
#   0) static TF          -> base_link -> hesai_lidar (lidar mount offset)
#   1) KISS-SLAM          -> odometry_node + slam_node + RViz
#
# Prerequisites:
#   - kiss-slam Python core installed (baked into the Docker image)
#   - kiss_slam_ros package built: colcon build --packages-select kiss_slam_ros

SESSION="kiss_slam"

SETUP="source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash"

# Lidar mount offset relative to base_link: x y z (m)  yaw pitch roll (rad).
# Placeholder — replace with the real XT16 mount pose on the Go2.
LIDAR_XYZ_RPY="0 0 0.10 0 0 0"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

# 0) Static transform: base_link -> hesai_lidar
tmux send-keys -t "$SESSION" \
    "$SETUP && ros2 run tf2_ros static_transform_publisher $LIDAR_XYZ_RPY base_link hesai_lidar" \
    Enter

# 1) KISS-SLAM launch (odometry_node + slam_node + RViz)
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "$SETUP && sleep 3 && ros2 launch kiss_slam_ros slam.launch.py topic:=/lidar_points use_sim_time:=false visualize:=true" \
    Enter

tmux select-layout -t "$SESSION" tiled
tmux attach-session -t "$SESSION"
