#!/bin/bash
# Live KISS-SLAM (odometry + loop closure + occupancy grid) on the Hesai XT16.
#
# Pane layout (tiled):
#   0) Hesai driver node  -> publishes /lidar_points
#   1) static TF          -> base_link -> hesai_lidar (lidar mount offset)
#   2) KISS-SLAM          -> odometry_node + slam_node + RViz
#
# Prerequisites:
#   - kiss-slam Python core installed: cd /workspace/go2_slam_ws/src/kiss-slam-ros2 && make editable
#   - kiss_slam_ros package built: colcon build --packages-select kiss_slam_ros

SESSION="hesai_kiss_slam"

SETUP="source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash"

# Lidar mount offset relative to base_link: x y z (m)  yaw pitch roll (rad).
# Placeholder — replace with the real XT16 mount pose on the Go2.
LIDAR_XYZ_RPY="0 0 0.10 0 0 0"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

# 0) Hesai driver (publishes /lidar_points, no RViz)
tmux send-keys -t "$SESSION" \
    "$SETUP && ros2 run hesai_ros_driver hesai_ros_driver_node 2>&1 | grep -v retcode" \
    Enter

# 1) Static transform: base_link -> hesai_lidar
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "$SETUP && ros2 run tf2_ros static_transform_publisher $LIDAR_XYZ_RPY base_link hesai_lidar" \
    Enter

# 2) KISS-SLAM launch (odometry_node + slam_node + RViz)
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "$SETUP && sleep 3 && ros2 launch kiss_slam_ros slam.launch.py topic:=/lidar_points use_sim_time:=false visualize:=true" \
    Enter

tmux select-layout -t "$SESSION" tiled
tmux attach-session -t "$SESSION"
