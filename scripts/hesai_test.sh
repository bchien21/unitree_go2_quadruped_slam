#!/bin/bash
SESSION="hesai_test"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

tmux send-keys -t "$SESSION" \
    "source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash && ros2 launch hesai_ros_driver start.py 2>&1 | grep -v retcode" \
    Enter

tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" \
    "sleep 3 && source /opt/ros/humble/setup.bash && rviz2" \
    Enter

tmux select-pane -t "$SESSION:.0"
tmux attach-session -t "$SESSION"

