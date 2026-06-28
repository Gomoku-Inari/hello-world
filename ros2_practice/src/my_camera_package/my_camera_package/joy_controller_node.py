import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String
from .mode_state_machine import ModeStateMachine  # 状態マシンをインポート

class JoyControllerNode(Node):
    def __init__(self):
        super().__init__('joy_controller')
        
        self.mode_publisher = self.create_publisher(String, '/current_mode', 10)

        # 🌟 自身のパブリッシュ関数をコールバックとして状態マシンに「教育」して内包
        self.state_machine = ModeStateMachine(
            on_mode_changed_callback=self._publish_mode
        )

        # トピック設定
        self.subscription = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        self.mode_subscription = self.create_subscription(String, '/current_mode', self.mode_sync_callback, 10)
        self.get_logger().info("ゲームパッド制御ノード（コールバックインジェクション版）が起動しました。")

    def _publish_mode(self, mode_str: str):
        self.get_logger().info("JoyControllerNode::_publish_mode")
        """状態マシンから自動で呼び出されるパブリッシュの実体"""
        msg = String(data=mode_str)
        self.mode_publisher.publish(msg)
        self.get_logger().info(f"【状態変化】 /current_mode にパブリッシュしました: {mode_str}")

    def mode_sync_callback(self, msg):
        self.state_machine.sync_mode(msg.data)

    def joy_callback(self, msg):
        # 🌟 ノード側は判定を見て「ただ設定を要求するだけ」になり、驚くほどスッキリ！
        if msg.buttons[0] == 1:
            self.state_machine.set_mode("gray")
        elif msg.buttons[1] == 1:
            self.state_machine.set_mode("color")
        elif msg.buttons[2] == 1:
            self.state_machine.set_mode("face")

def main(args=None):
    rclpy.init(args=args)
    node = JoyControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
