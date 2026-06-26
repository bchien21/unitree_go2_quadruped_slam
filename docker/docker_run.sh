#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Safely get the home directory of the user who logged in via SSH, 
# even if this script is executed with 'sudo'
REAL_HOME=$(eval echo ~${SUDO_USER:-$USER})
XAUTH_FILE="$REAL_HOME/.Xauthority"

docker run -it --rm \
    --name go2_slam_dev \
    --network=host \
    --ipc=host \
    --pid=host \
    --shm-size=1gb \
    --env DISPLAY="$DISPLAY" \
    --env QT_X11_NO_MITSHM=1 \
    --env XAUTHORITY=/root/.Xauthority \
    --env RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    --volume "$XAUTH_FILE:/root/.Xauthority:ro" \
    --volume "$PROJECT_ROOT/go2_slam_ws":/workspace/go2_slam_ws:rw \
    --volume "$PROJECT_ROOT/kiss-slam-ros2":/workspace/kiss-slam-ros2:rw \
    --volume "$PROJECT_ROOT/scripts":/workspace/scripts:rw \
    --volume "$PROJECT_ROOT/rosbags":/workspace/rosbags:rw \
    go2_slam:humble
