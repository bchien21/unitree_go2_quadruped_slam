#!/bin/bash
SESSION="hesai_test"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

tmux send-keys -t "$SESSION" \
    "source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash && ros2 launch hesai_ros_driver start.py 2>&1 | grep -v retcode" \
    Enter

tmux attach-session -t "$SESSION"

