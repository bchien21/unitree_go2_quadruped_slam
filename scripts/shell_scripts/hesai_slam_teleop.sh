#!/bin/bash
SESSION="hesai_slam_teleop"
SOURCE_CMD="source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

# Pane 0: Hesai lidar driver
tmux send-keys -t "$SESSION" \
    "$SOURCE_CMD && ros2 launch hesai_ros_driver start.py 2>&1 | grep -v retcode" \
    Enter

# Pane 1: SLAM (headless — no viz over SSH)
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "sleep 5 && $SOURCE_CMD && ros2 launch go2_slam slam_hesai.launch.py use_rtabmap_viz:=false 2>&1 | grep -v 'ddsi_udp_conn_write\|retcode'" \
    Enter

# Pane 2: Teleop
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "sleep 8 && python3 /workspace/scripts/python_scripts/teleop.py" \
    Enter

tmux select-pane -t "$SESSION:.2"
tmux attach-session -t "$SESSION"
