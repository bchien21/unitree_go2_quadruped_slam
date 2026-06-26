FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# ── ROS 2 core packages ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-tf2-ros \
    ros-humble-rviz2 \
    ros-humble-rclpy \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# ── Nav2 navigation stack ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-nav2-bringup \
    ros-humble-nav2-bt-navigator \
    ros-humble-nav2-lifecycle-manager \
    && rm -rf /var/lib/apt/lists/*

# ── Hesai SDK build deps ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libboost-all-dev \
    libyaml-cpp-dev \
    libpcap-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ── KISS-SLAM build deps (Eigen, SuiteSparse, newer CMake) ───────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeigen3-dev \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir \
    "cmake>=3.24" \
    scikit-build-core \
    pyproject_metadata \
    pathspec \
    pybind11 \
    ninja \
    kiss-icp \
    kiss-slam \
    scipy

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
