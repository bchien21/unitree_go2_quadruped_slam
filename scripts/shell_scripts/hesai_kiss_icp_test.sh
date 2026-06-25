#!/bin/bash
# Live KISS-ICP lidar odometry on the Hesai XT16 point cloud stream.
#
# Pane layout (tiled):
#   0) Hesai driver node  -> publishes /lidar_points
#   1) static TF          -> base_link -> hesai_lidar (lidar mount offset)
#   2) KISS-ICP + RViz    -> consumes /lidar_points, publishes kiss/odometry + local map
#
# Notes:
#   - use_sim_time:=false  : required for LIVE data (the launch defaults to true for bag playback).
#   - lidar_odom_frame is left at KISS-ICP's default 'odom_lidar' so the bundled
#     RViz config (Fixed Frame: odom_lidar) works out of the box.
#   - invert_odom_tf:=false : publishes the conventional odom_lidar -> base_link TF.

SESSION="hesai_kiss_icp"

# Sourced at the start of every pane (run inside the dev container).
SETUP="source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash"

# Lidar mount offset relative to base_link: x y z (m)  yaw pitch roll (rad).
# Placeholder height of 0.10 m - replace with the real XT16 mount pose on the Go2.
LIDAR_XYZ_RPY="0 0 0.10 0 0 0"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

# 0) Hesai driver (no RViz - KISS-ICP brings its own)
tmux send-keys -t "$SESSION" \
    "$SETUP && ros2 run hesai_ros_driver hesai_ros_driver_node 2>&1 | grep -v retcode" \
    Enter

# 1) Static transform: base_link -> hesai_lidar
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "$SETUP && ros2 run tf2_ros static_transform_publisher $LIDAR_XYZ_RPY base_link hesai_lidar" \
    Enter

# 2) KISS-ICP odometry + RViz (wait for the driver to come up first)
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "$SETUP && sleep 3 && ros2 launch kiss_icp odometry.launch.py topic:=/lidar_points base_frame:=base_link publish_odom_tf:=true invert_odom_tf:=false use_sim_time:=false visualize:=true" \
    Enter

tmux select-layout -t "$SESSION" tiled
tmux attach-session -t "$SESSION"
