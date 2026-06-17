FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# ── ROS 2 SLAM / sensor packages ────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rtabmap-ros \
    ros-humble-rtabmap-slam \
    ros-humble-rtabmap-viz \
    ros-humble-realsense2-camera \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-tf2-ros \
    ros-humble-cv-bridge \
    ros-humble-rviz2 \
    ros-humble-rclpy \
    python3-opencv \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# ── Hesai SDK build deps ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libboost-all-dev \
    libyaml-cpp-dev \
    libpcap-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ── Quality-of-life tools ───────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    nano \
    tmux \
    htop \
    bash-completion \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# ── ROS environment defaults ────────────────────────────────────────────────
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=0

WORKDIR /workspace

# ── Shell environment ────────────────────────────────────────────────────────
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo '[ -f /workspace/go2_slam_ws/install/setup.bash ] && source /workspace/go2_slam_ws/install/setup.bash' >> /root/.bashrc

CMD ["bash"]
