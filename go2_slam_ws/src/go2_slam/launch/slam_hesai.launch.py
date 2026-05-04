"""
LiDAR-only SLAM using Hesai XT16 + RTAB-Map icp_odometry.

Usage:
  ros2 launch go2_slam slam_lidar.launch.py
  ros2 launch go2_slam slam_lidar.launch.py localize_only:=true   # use existing map
  ros2 launch go2_slam slam_lidar.launch.py reset_map:=true       # start fresh

Assumes Hesai XT16 driver is already running and publishing:
  /lidar_points  (sensor_msgs/PointCloud2, frame_id: hesai_lidar)
"""

import os

import platform

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _make_rtabmap_nodes(context, *args, **kwargs):
    """Mem/IncrementalMemory must be false when localize_only (load map, no new nodes)."""
    localize_only_str = LaunchConfiguration('localize_only').perform(context)
    incremental = 'false' if localize_only_str == 'true' else 'true'
    map_db_path = os.path.expanduser(LaunchConfiguration('map_db_path').perform(context))
    lidar_topic_str = LaunchConfiguration('lidar_topic').perform(context)
    use_viz_str = LaunchConfiguration('use_rtabmap_viz').perform(context)

    rtabmap = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[{
            'frame_id':         'base_link',
            'odom_frame_id':    'odom',
            'subscribe_depth':  False,
            'subscribe_rgb':    False,
            'subscribe_scan_cloud': True,
            'approx_sync':      False,
            'Mem/IncrementalMemory': incremental,
            'Mem/InitWIthSavedParams': 'true',
            'database_path':    map_db_path,
            'Grid/3D':          'true',
            'Grid/RangeMin':    '0.5',
            'Grid/RangeMax':    '15.0',
            'Reg/Strategy':     '1',
            'Reg/Force3DoF':    'true',
        }],
        remappings=[
            ('scan_cloud', lidar_topic_str),
        ],
    )

    rtabmap_viz = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        output='screen',
        parameters=[{
            'frame_id':     'base_link',
            'odom_frame_id': 'odom',
            'subscribe_scan_cloud': True,
        }],
        remappings=[
            ('scan_cloud', lidar_topic_str),
        ],
    )

    if use_viz_str.lower() == 'true':
        return [rtabmap, rtabmap_viz]
    return [rtabmap]


def generate_launch_description():
    # ── Arguments ──────────────────────────────────────────────────────────
    localize_only_arg = DeclareLaunchArgument(
        'localize_only', default_value='false',
        description='true = localization only (existing map), false = build new map'
    )
    reset_map_arg = DeclareLaunchArgument(
        'reset_map', default_value='false',
        description='true = delete existing map database and start fresh'
    )
    # Topic published by Hesai ROS2 driver (HesaiLidar_ROS2_SDK default)
    lidar_topic_arg = DeclareLaunchArgument(
        'lidar_topic', default_value='/lidar_points',
        description='PointCloud2 topic from Hesai XT16 driver'
    )
    lidar_frame_arg = DeclareLaunchArgument(
        'lidar_frame', default_value='hesai_lidar',
        description='TF frame id published by the Hesai driver'
    )
    map_db_path_arg = DeclareLaunchArgument(
        'map_db_path', default_value='~/.ros/rtabmap.db',
        description='Path to the RTAB-Map database file'
    )
    use_rtabmap_viz_arg = DeclareLaunchArgument(
        'use_rtabmap_viz', default_value='true',
        description='Set false on headless Jetson to skip the heavy GUI'
    )

    lidar_topic = LaunchConfiguration('lidar_topic')
    lidar_frame = LaunchConfiguration('lidar_frame')

    # ── Static TF: base_link → hesai_lidar ─────────────────────────────────
    # Source: official Go2 URDF body box = 0.3762 × 0.0935 × 0.114 m
    #   → top surface at z = +0.057 m from base_link
    # Hesai XT16 sits on a bracket on top; centre of sensor ≈ z = 0.10 m.
    # Adjust z if your bracket is taller/shorter.
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_lidar_tf',
        arguments=[
            '0.0', '0.0', '0.10',   # x(fwd) y(left) z(up)  — metres
            '0.0', '0.0', '0.0',    # roll   pitch    yaw    — radians
            'base_link', lidar_frame,
        ],
    )

    # ── ICP Odometry (LiDAR wheel-odometry-free) ────────────────────────────
    icp_odometry = Node(
        package='rtabmap_odom',
        executable='icp_odometry',
        name='icp_odometry',
        output='screen',
        parameters=[{
            'frame_id':       'base_link',
            'odom_frame_id':  'odom',
            'wait_for_transform': 0.2,
            # ICP parameters tuned for XT16 (16-beam sparse)
            'Icp/PointToPlane':         'true',
            'Icp/Iterations':           '10',
            'Icp/VoxelSize':            '0.1',
            'Icp/DownsamplingStep':     '1',
            'Icp/MaxCorrespondenceDistance': '0.3',
            'Icp/PM':                   'true',
            'Icp/PMOutlierRatio':       '0.7',
            'Odom/ScanKeyFrameThr':     '0.4',
            'OdomF2M/ScanSubtractRadius': '0.1',
            'OdomF2M/ScanMaxSize':      '15000',
            'publish_null_when_lost':   False,
        }],
        remappings=[
            ('scan_cloud', lidar_topic),
        ],
    )

    actions = [
        localize_only_arg,
        reset_map_arg,
        lidar_topic_arg,
        lidar_frame_arg,
        map_db_path_arg,
        use_rtabmap_viz_arg,
        static_tf,
        icp_odometry,
        OpaqueFunction(function=_make_rtabmap_nodes),
    ]
    # Old conda/libstdc++ workaround only needed on x86_64 laptops. Skip on
    # aarch64 Jetsons, where the path doesn't exist and would break launch.
    if platform.machine() == 'x86_64' and os.path.exists(
            '/usr/lib/x86_64-linux-gnu/libstdc++.so.6'):
        actions.insert(0, SetEnvironmentVariable(
            'LD_PRELOAD', '/usr/lib/x86_64-linux-gnu/libstdc++.so.6'))
    return LaunchDescription(actions)
