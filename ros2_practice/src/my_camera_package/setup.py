from setuptools import find_packages, setup

package_name = 'my_camera_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/camera_system.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gomokuinari',
    maintainer_email='gomokuinari@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # 画像変換処理ノード
            'img_processor = my_camera_package.img_processor:main',
            # モード変換(gesture)ノード
            'gesture_controller = my_camera_package.gesture_controller_node:main',
            # モード変換(ゲームパッド)ノード
            'joy_controller = my_camera_package.joy_controller_node:main',
            'joy_test_node = my_camera_package.joy_test_node:main',
        ],
    },
)
