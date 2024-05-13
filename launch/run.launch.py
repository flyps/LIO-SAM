import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share_dir = get_package_share_directory('lio_sam')
    parameter_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz_config_file = os.path.join(share_dir, 'config', 'rviz2.rviz')

    params_declare = [
        DeclareLaunchArgument('use_sim_time',
                              default_value=TextSubstitution(text="true"),
                              description="Use simulation (Gazebo) clock if true."),

        DeclareLaunchArgument('params_file',
                              default_value=os.path.join(share_dir, 'config',
                                                         'simulation_params.yaml'),
                              description='FPath to the ROS2 parameters file to use.'),
    ]

    # provide map -> odom transform using GNSS
    odom_node_path = FindPackageShare(package='jablka_odometry').find('jablka_odometry')
    start_global_odometry = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(odom_node_path, "launch", "run.launch.py")),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'start_ekf_local': 'false',
        }.items()
    )

    # LIO-SAM provides the local odometry
    start_lio_sam = GroupAction([
        Node(
            package='lio_sam',
            executable='lio_sam_imuPreintegration',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_imageProjection',
            name='lio_sam_imageProjection',
            parameters=[parameter_file],
            output='screen',
            remappings=[
                ('/points', 'lidar/points')
            ]
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_featureExtraction',
            name='lio_sam_featureExtraction',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_mapOptimization',
            name='lio_sam_mapOptimization',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        )
    ])

    return LaunchDescription([
        *params_declare,
        start_global_odometry,
        start_lio_sam
    ])