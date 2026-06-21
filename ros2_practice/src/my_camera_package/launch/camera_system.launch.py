from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. カメラドライバ
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='camera_driver',
            parameters=[{
                'video_device': '/dev/video0',
                'image_size': [640, 480],  # 🌟
                'pixel_format': 'YUYV'
            }]
        ),
        
        # 2. ゲームパッドの公式ドライバノード（復活！）
        Node(
            package='joy',
            executable='joy_node',
            name='joy_driver'
        ),
        
        # 🌟 3. ゲームパッドの翻訳＆エッジ制御ノード（新規追加！）
        Node(
            package='my_camera_package',
            executable='joy_controller',
            name='my_joy_controller'
        ),
        
        # 4. ジェスチャー制御ノード（そのまま常駐）
        Node(
            package='my_camera_package',
            executable='gesture_controller',
            name='my_gesture_controller'
        ),
        
        # 5. 自作の画像処理ノード（変更なし、トピックを待つだけ）
        Node(
            package='my_camera_package',
            executable='img_processor',
            name='my_processor'
        ),
        
        # 6. 表示モニターツール
        Node(
            package='image_view',
            executable='image_view',
            name='my_viewer',
            remappings=[
                ('image', '/image_gray')
            ]
        )
    ])
