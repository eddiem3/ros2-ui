from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_flask_ui',
            executable='kitti_publisher',
            name='kitti_publisher',
            output='screen'
        ),
        Node(
            package='ros2_flask_ui',
            executable='segmentation_node',
            name='segmentation_node',
            output='screen'
        ),
        Node(
            package='ros2_flask_ui',
            executable='app',
            name='flask_webapp',
            output='screen'
        )
    ])
