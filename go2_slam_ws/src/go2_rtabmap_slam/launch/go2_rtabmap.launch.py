import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _rtabmap_nodes(context, *args, **kwargs):
    delete_db = LaunchConfiguration('delete_db_on_start').perform(context)
    rtabmap_args = '--delete_db_on_start' if delete_db.lower() == 'true' else ''

    rtabmap_launch_dir = get_package_share_directory('rtabmap_launch')
    rtabmap_viz_launch_dir = get_package_share_directory('rtabmap_viz')

    rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rtabmap_launch_dir, 'launch', 'rtabmap.launch.py')
        ),
        launch_arguments={
            # Frames
            'frame_id': 'base_link',

            # Disable camera inputs — LiDAR only
            'subscribe_depth': 'false',
            'subscribe_rgb': 'false',
            'subscribe_stereo': 'false',

            # 3D LiDAR input
            'subscribe_scan_cloud': 'true',
            'scan_cloud_topic': '/lidar_points',

            # External odometry from the Go2's utlidar system — disable
            # RTAB-Map's own odometry nodes so this topic is actually used
            'icp_odometry': 'false',
            'visual_odometry': 'false',
            'odom_topic': '/utlidar/robot_odom',

            # Allow small time differences between odom and point cloud
            'approx_sync': 'true',

            # Use ICP for loop-closure registration
            'Reg/Strategy': '1',

            # ICP settings
            'Icp/PointToPlane': 'true',
            'Icp/VoxelSize': '0.1',
            'Icp/MaxCorrespondenceDistance': '1.0',
            'Icp/Iterations': '30',

            # Graph/mapping settings
            'RGBD/NeighborLinkRefining': 'true',
            'RGBD/ProximityBySpace': 'true',
            'RGBD/AngularUpdate': '0.05',
            'RGBD/LinearUpdate': '0.05',
            'Mem/NotLinkedNodesKept': 'false',

            'rtabmap_args': rtabmap_args,
        }.items(),
    )

    rtabmap_viz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rtabmap_viz_launch_dir, 'launch', 'rtabmap_viz.launch.py')
        ),
        launch_arguments={
            'frame_id': 'base_link',
            'subscribe_scan_cloud': 'true',
            'scan_cloud_topic': '/lidar_points',
            'subscribe_odom_info': 'true',
        }.items(),
    )

    return [rtabmap, rtabmap_viz]


def generate_launch_description():
    delete_db_arg = DeclareLaunchArgument(
        'delete_db_on_start',
        default_value='true',
        description='Delete the RTAB-Map database on start (fresh mapping session)',
    )

    # Static TF: base_link → hesai_lidar
    # Adjust x, y, z (metres) and yaw, pitch, roll (radians) to match
    # the physical mount position of the Hesai LiDAR on the Go2 body.
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_hesai_lidar',
        arguments=[
            '0.0',   # x  (forward)
            '0.0',   # y  (left)
            '0.30',  # z  (up) — approx height of LiDAR mount above body centre
            '0.0',   # yaw
            '0.0',   # pitch
            '0.0',   # roll
            'base_link',
            'hesai_lidar',
        ],
    )

    return LaunchDescription([
        delete_db_arg,
        static_tf,
        OpaqueFunction(function=_rtabmap_nodes),
    ])
