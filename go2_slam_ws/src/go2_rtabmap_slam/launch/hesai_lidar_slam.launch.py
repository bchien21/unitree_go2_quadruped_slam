from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


# Topic names
LIDAR_TOPIC = '/lidar_points'
ODOM_TOPIC = '/utlidar/robot_odom'

# Frame IDs
ROBOT_BASE_FRAME = 'base_link'
LIDAR_FRAME = 'hesai_lidar'


def _make_rtabmap_nodes(context, *_, **__):
    reset_map = LaunchConfiguration('reset_map').perform(context) == 'true'
    use_viz = LaunchConfiguration('use_rtabmap_viz').perform(context) == 'true'

    rtabmap_args = ['-d'] if reset_map else []

    rtabmap = Node(
        package='rtabmap_slam', executable='rtabmap', output='screen',
        parameters=[{
            'frame_id': ROBOT_BASE_FRAME,
            'odom_frame_id': 'odom',
            'subscribe_depth': False,
            'subscribe_rgb': False,
            'subscribe_rgbd': False,
            'subscribe_scan': False,
            'subscribe_scan_cloud': True,
            'approx_sync': True,

            'Reg/Strategy': '1',
            'Reg/Force3DoF': 'false',
            'RGBD/NeighborLinkRefining': 'true',
            'ICP/VoxelSize': '0.2',
            'ICP/PointToPlane': 'true',
            'ICP/MaxCorrespondenceDistance': '0.3',
            'Mem/UseOdomGravity': 'true',
        }],
        remappings=[
            ('scan_cloud', LIDAR_TOPIC),
            ('odom', ODOM_TOPIC),
        ],
        arguments=rtabmap_args,
    )

    nodes = [rtabmap]

    if use_viz:
        nodes.append(Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=[{
                'frame_id': ROBOT_BASE_FRAME,
                'odom_frame_id': 'odom',
                'subscribe_depth': False,
                'subscribe_rgb': False,
                'subscribe_scan_cloud': True,
                'approx_sync': True,
            }],
            remappings=[
                ('scan_cloud', LIDAR_TOPIC),
                ('odom', ODOM_TOPIC),
            ],
        ))

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'reset_map', default_value='false',
            description='true = delete existing map database and start fresh',
        ),
        DeclareLaunchArgument(
            'use_rtabmap_viz', default_value='true',
            description='Set false on headless systems (e.g. Jetson) to skip the GUI',
        ),

        # 1. Odom-to-TF bridge (publishes odom -> base_link on /tf)
        Node(
            package='go2_rtabmap_slam',
            executable='unitree_odom_to_tf',
            name='unitree_odom_to_tf',
            output='screen',
        ),

        # 2. Static Transform Publisher (base_link -> hesai_lidar)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_tf',
            arguments=['0', '0', '0.10', '0', '0', '0', ROBOT_BASE_FRAME, LIDAR_FRAME],
        ),

        # 3. RTAB-Map SLAM + optional visualization
        OpaqueFunction(function=_make_rtabmap_nodes),
    ])