#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_dir = get_package_share_directory('ros_mqtt_bridge_node')
    
    return LaunchDescription([
        # 启动发送节点
        Node(
            package='ros_mqtt_bridge_node',
            executable='zip_sender',
            name='zip_sender',
            parameters=[
                {'mqtt_broker_host': '120.24.79.108'},
                {'mqtt_broker_port': 1883},
                {'mqtt_username': 'zone'},
                {'mqtt_password': 'NeverGiveUp'}
            ],
            output='screen'
        ),
        
        # 启动接收节点
        Node(
            package='ros_mqtt_bridge_node',
            executable='zip_receiver',
            name='zip_receiver',
            parameters=[
                {'mqtt_broker_host': '120.24.79.108'},
                {'mqtt_broker_port': 1883},
                {'mqtt_username': 'zone'},
                {'mqtt_password': 'NeverGiveUp'},
                {'output_dir': os.path.expanduser('~/received_files')}
            ],
            output='screen'
        )
    ])