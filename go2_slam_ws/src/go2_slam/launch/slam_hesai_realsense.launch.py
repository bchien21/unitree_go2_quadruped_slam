"""
LiDAR + RealSense D435i fusion SLAM using RTAB-Map.

Runs:
  1. realsense2_camera  — publishes RGB + aligned depth + IMU
  2. static_tf          — base_link → hesai_lidar and base_link → camera_link
  3. icp_odometry       — LiDAR-based odometry (Hesai XT16)
  4. rtabmap            — loop-closure SLAM fusing point cloud + RGB-D
  5. rtabmap_viz        — GUI visualizer

Usage:
  ros2 launch go2_slam slam_lidar_camera.launch.py
  ros2 launch go2_slam slam_lidar_camera.launch.py localize_only:=true
  ros2 launch go2_slam slam_lidar_camera.launch.py reset_map:=true
  ros2 launch go2_slam slam_lidar_camera.launch.py remote_camera:=true

Assumes Hesai XT16 driver is already running and publishing:
  /lidar_points  (sensor_msgs/PointCloud2, frame_id: hesai_lidar)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os
import platform


def _make_rtabmap_nodes(context, *args, **kwargs):
    localize_only_str = LaunchConfiguration('localize_only').perform(context)
    incremental = 'false' if localize_only_str == 'true' else 'true'
    map_db_path = os.path.expanduser(LaunchConfiguration('map_db_path').perform(context))
    lidar_topic = LaunchConfiguration('lidar_topic').perform(context)
    use_viz_str = LaunchConfiguration('use_rtabmap_viz').perform(context)

    rtabmap = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[{
            'frame_id':             'base_link',
            'odom_frame_id':        'odom',
            'subscribe_depth':      True,
            'subscribe_rgb':        True,
            'subscribe_scan_cloud': True,
            'approx_sync':          True,
            'approx_sync_max_interval': 0.1,
            'Mem/IncrementalMemory': incremental,
            'Mem/InitWIthSavedParams': 'true',
            'database_path':        map_db_path,
            'Vis/MinInliers':       '15',
            'Vis/InlierDistance':   '0.1',
            'Grid/3D':              'true',
            'Grid/RangeMin':        '0.5',
            'Grid/RangeMax':        '15.0',
            'Grid/NormalsSegmentation': 'false',
            'Reg/Strategy':         '3',
            'Reg/Force3DoF':        'true',
        }],
        remappings=[
            ('scan_cloud',   lidar_topic),
            ('rgb/image',    '/camera/color/image_raw'),
            ('rgb/camera_info', '/camera/color/camera_info'),
            ('depth/image',  '/camera/aligned_depth_to_color/image_raw'),
        ],
    )

    rtabmap_viz = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        output='screen',
        parameters=[{
            'frame_id':             'base_link',
            'odom_frame_id':        'odom',
            'subscribe_scan_cloud': True,
            'subscribe_depth':      True,
            'subscribe_rgb':        True,
        }],
        remappings=[
            ('scan_cloud',   lidar_topic),
            ('rgb/image',    '/camera/color/image_raw'),
            ('rgb/camera_info', '/camera/color/camera_info'),
            ('depth/image',  '/camera/aligned_depth_to_color/image_raw'),
        ],
    )

    if use_viz_str.lower() == 'true':
        return [rtabmap, rtabmap_viz]
    return [rtabmap]


def generate_launch_description():
    # ── Arguments ──────────────────────────────────────────────────────────
    localize_only_arg = DeclareLaunchArgument(
        'localize_only', default_value='false',
        description='true = localization only using existing map'
    )
    reset_map_arg = DeclareLaunchArgument(
        'reset_map', default_value='false',
        description='true = delete db and start fresh mapping session'
    )
    lidar_topic_arg = DeclareLaunchArgument(
        'lidar_topic', default_value='/lidar_points',
        description='PointCloud2 topic from Hesai XT16'
    )
    lidar_frame_arg = DeclareLaunchArgument(
        'lidar_frame', default_value='hesai_lidar',
        description='TF frame id for the Hesai XT16'
    )
    map_db_path_arg = DeclareLaunchArgument(
        'map_db_path', default_value='~/.ros/rtabmap.db',
        description='Path to RTAB-Map database'
    )
    remote_camera_arg = DeclareLaunchArgument(
        'remote_camera', default_value='false',
        description='true = D435 driver already running on robot, skip local launch'
    )
    use_rtabmap_viz_arg = DeclareLaunchArgument(
        'use_rtabmap_viz', default_value='true',
        description='Set false on headless Jetson to skip the heavy GUI'
    )

    lidar_topic   = LaunchConfiguration('lidar_topic')
    lidar_frame   = LaunchConfiguration('lidar_frame')
    remote_camera = LaunchConfiguration('remote_camera')

    # ── RealSense D435 (local) ───────────────────────────────────────────────
    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('realsense2_camera'), '/launch/rs_launch.py'
        ]),
        launch_arguments={
            'enable_color':                 'true',
            'enable_depth':                 'true',
            'enable_infra1':                'false',
            'enable_infra2':                'false',
            'align_depth.enable':           'true',
            'enable_gyro':                  'true',
            'enable_accel':                 'true',
            'unite_imu_method':             '1',
            'depth_module.depth_profile':   '640x480x30',
            'rgb_camera.color_profile':     '640x480x30',
        }.items(),
        condition=UnlessCondition(remote_camera),
    )

    # ── Static TF: base_link → hesai_lidar ─────────────────────────────────
    tf_base_to_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_lidar_tf',
        arguments=[
            '0.0',  '0.0',  '0.10',
            '0.0',  '0.0',  '0.0',
            'base_link', lidar_frame,
        ],
    )

    # ── Static TF: base_link → camera_link ─────────────────────────────────
    tf_base_to_camera = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_camera_tf',
        arguments=[
            '0.285',  '0.0',  '0.01',
            '0.0',    '0.0',  '0.0',
            'base_link', 'camera_link',
        ],
    )

    # ── ICP Odometry ─────────────────────────────────────────────────────────
    icp_odometry = Node(
        package='rtabmap_odom',
        executable='icp_odometry',
        name='icp_odometry',
        output='screen',
        parameters=[{
            'frame_id':        'base_link',
            'odom_frame_id':   'odom',
            'wait_for_transform': 0.2,
            'Icp/PointToPlane':              'true',
            'Icp/Iterations':                '10',
            'Icp/VoxelSize':                 '0.1',
            'Icp/MaxCorrespondenceDistance': '0.3',
            'Icp/PM':                        'true',
            'Icp/PMOutlierRatio':            '0.7',
            'Odom/ScanKeyFrameThr':          '0.4',
            'OdomF2M/ScanSubtractRadius':    '0.1',
            'OdomF2M/ScanMaxSize':           '15000',
            'publish_null_when_lost':        False,
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
        remote_camera_arg,
        use_rtabmap_viz_arg,
        realsense,
        tf_base_to_lidar,
        tf_base_to_camera,
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
