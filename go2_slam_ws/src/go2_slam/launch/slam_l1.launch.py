"""SLAM using the Go2's built-in L1 lidar (/utlidar/cloud_deskewed) + Unitree odometry.

Architecture:

  /utlidar/cloud_deskewed (PointCloud2, frame=utlidar_lidar, ~15 Hz)
  /utlidar/robot_odom    (Odometry, odom->base_link, ~150 Hz)
        |
        | unitree_odom_to_tf.py  (bridge Odometry -> /tf)
        v
  /tf  odom -> base_link  +  /tf_static base_link -> utlidar_lidar
        |
        v
  rtabmap_slam (subscribe_scan_cloud=true, external odom)
        -> /map, /mapData, /cloud_map, /tf map->odom

Usage (live):
  ros2 launch go2_slam slam_l1.launch.py reset_map:=true

Usage (bag replay):
  ros2 launch go2_slam slam_l1.launch.py use_sim_time:=true reset_map:=true
  ros2 bag play <bag_path> --clock
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def _make_rtabmap(context, *_, **__):
    localize_only = LaunchConfiguration('localize_only').perform(context) == 'true'
    incremental = 'false' if localize_only else 'true'
    map_db_path = os.path.expanduser(
        LaunchConfiguration('map_db_path').perform(context))
    reset_map = LaunchConfiguration('reset_map').perform(context) == 'true'
    use_viz = LaunchConfiguration('use_rtabmap_viz').perform(context) == 'true'
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context) == 'true'

    rtabmap_params = {
        'use_sim_time': use_sim_time,
        'frame_id': 'base_link',
        'odom_frame_id': 'odom',
        'map_frame_id': 'map',
        'publish_tf': True,
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_scan': False,
        'subscribe_scan_cloud': True,
        'subscribe_odom_info': False,
        'approx_sync': True,
        'queue_size': 30,
        'wait_for_transform': 0.5,
        'database_path': map_db_path,
        'Mem/IncrementalMemory': incremental,
        'Mem/InitWMWithAllNodes': 'false' if not localize_only else 'true',
        'Rtabmap/DetectionRate': '1',
        'Reg/Strategy': '1',
        'Reg/Force3DoF': 'true',
        'RGBD/NeighborLinkRefining': 'true',
        'RGBD/ProximityBySpace': 'true',
        'RGBD/ForceOdom3DoF': 'true',
        'RGBD/CreateOccupancyGrid': 'true',
        'Icp/Strategy': '1',
        'Icp/VoxelSize': '0.05',
        'Icp/PointToPlane': 'true',
        'Icp/MaxTranslation': '0.4',
        'Icp/MaxCorrespondenceDistance': '0.2',
        'Icp/RangeMax': '7.5',
        'Icp/CorrespondenceRatio': '0.15',
        'Icp/ReciprocalCorrespondences': 'true',
        'Icp/FiltersEnabled': '3',
        'Optimizer/Strategy': '2',
        'Grid/Sensor': '0',
        'Grid/RangeMax': '7.5',
        'Grid/RangeMin': '0.5',
        'Grid/CellSize': '0.05',
        'Grid/3D': 'false',
        'Grid/FromDepth': 'false',
        'Grid/RayTracing': 'true',
    }

    remappings = [
        ('scan_cloud', '/utlidar/cloud_deskewed'),
        ('odom', '/utlidar/robot_odom'),
    ]

    rtabmap_args = ['-d'] if reset_map and not localize_only else []

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[rtabmap_params],
        remappings=remappings,
        arguments=rtabmap_args,
    )

    actions = [rtabmap_node]

    if use_viz:
        actions.append(Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            name='rtabmap_viz',
            output='screen',
            parameters=[rtabmap_params],
            remappings=remappings,
        ))

    return actions


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Set true for bag replay (requires ros2 bag play --clock)'
    )
    localize_only_arg = DeclareLaunchArgument(
        'localize_only', default_value='false',
        description='true => load map and localize only; false => build new map'
    )
    reset_map_arg = DeclareLaunchArgument(
        'reset_map', default_value='false',
        description='true => delete the existing .db before starting'
    )
    map_db_path_arg = DeclareLaunchArgument(
        'map_db_path', default_value='~/.ros/go2_rtabmap.db',
        description='Where to store/load the rtabmap database'
    )
    use_rtabmap_viz_arg = DeclareLaunchArgument(
        'use_rtabmap_viz', default_value='false',
        description='true on a machine with a display; false on the headless Jetson'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    tf_base_to_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_utlidar',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=[
            '0.285', '0.0', '0.125',
            '0.0',   '0.0', '0.0',
            'base_link', 'utlidar_lidar'
        ],
    )

    odom_to_tf = Node(
        package='go2_slam',
        executable='unitree_odom_to_tf.py',
        name='unitree_odom_to_tf',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        use_sim_time_arg,
        localize_only_arg,
        reset_map_arg,
        map_db_path_arg,
        use_rtabmap_viz_arg,
        tf_base_to_lidar,
        odom_to_tf,
        OpaqueFunction(function=_make_rtabmap),
    ])
