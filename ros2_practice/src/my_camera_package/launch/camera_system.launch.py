from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. カメラドライバノード
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='camera_driver',
            parameters=[{
                'video_device': '/dev/video0',
                'image_size': [640, 480],
                'pixel_format': 'YUYV'
            }]
        ),
        
        # 2. ゲームパッドドライバノード
        Node(
            package='joy',
            executable='joy_node',
            name='joy_driver'
        ),
        
        # 3. 自作の画像処理ノード
        Node(
            package='my_camera_package',
            executable='img_processor',
            name='my_processor'
        ),
        
        # 4. 表示ツールノード
        Node(
            package='image_view',
            executable='image_view',
            name='my_viewer',
            remappings=[
                ('image', '/image_gray')
            ]
        )
    ])
