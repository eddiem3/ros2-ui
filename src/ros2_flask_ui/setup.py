from setuptools import setup
import os
from glob import glob

package_name = 'ros2_flask_ui'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        # Include web templates/static files
        (os.path.join('share', package_name, 'templates'), glob('templates/*')),
        (os.path.join('share', package_name, 'static', 'css'), glob('static/css/*')),
        (os.path.join('share', package_name, 'static', 'js'), glob('static/js/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Dev',
    maintainer_email='dev@example.com',
    description='ROS2 UI via Flask and WebSockets, playing KITTI semantic segmentation results',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'kitti_publisher = ros2_flask_ui.kitti_publisher:main',
            'segmentation_node = ros2_flask_ui.segmentation_node:main',
            'app = ros2_flask_ui.app:main'
        ],
    },
)
