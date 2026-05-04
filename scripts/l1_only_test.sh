#!/bin/bash
SESSION="l1_slam_test"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION"
tmux set-option -t "$SESSION" mouse on

tmux send-keys -t "$SESSION" \
    'source /opt/ros/humble/setup.bash && source /workspace/go2_slam_ws/install/setup.bash && ros2 launch go2_slam slam_l1.launch.py use_sim_time:=true reset_map:=true use_rtabmap_viz:=true 2>&1 | grep -v ddsi_udp_conn_write' \
    Enter

tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" \
    'sleep 5 && source /opt/ros/humble/setup.bash && ros2 bag play /workspace/rosbags/go2_fastlio_bag_5 --clock' \
    Enter

tmux select-pane -t "$SESSION:.0"
tmux attach-session -t "$SESSION"
