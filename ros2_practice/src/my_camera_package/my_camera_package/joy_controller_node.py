import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String

class JoyController(Node):
    def __init__(self):
        super().__init__('joy_controller')
        
        self.current_mode = "gray"

        # ゲームパッドのトピックを購読
        self.subscription = self.create_subscription(
            Joy, '/joy', self.joy_callback, 10)
        
        # 🌟 追加：現在のモードを自分自身でも購読して「記憶を同期」させる
        self.mode_subscription = self.create_subscription(
            String, '/current_mode', self.mode_sync_callback, 10)
        
        # 共通言語である /current_mode にパブリッシュするパブリッシャ
        self.mode_publisher = self.create_publisher(String, '/current_mode', 10)
        
        self.get_logger().info("ゲームパッド制御ノード（同期版）が起動しました。")

    # 🌟 追加：誰かがモードを変えたら、自分の変数も最新に上書きする
    def mode_sync_callback(self, msg):
        self.current_mode = msg.data

    def joy_callback(self, msg):
        new_mode = self.current_mode

        # 各ボタンのインデックス（0, 1, 2）を明示的に指定
        if msg.buttons[0] == 1:
            new_mode = "gray"
        elif msg.buttons[1] == 1:
            new_mode = "color"
        elif msg.buttons[2] == 1:
            new_mode = "face"

        # 記憶が同期されているため、ここのエッジ判定が常に正しく動きます
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            
            msg_str = String()
            msg_str.data = self.current_mode
            self.mode_publisher.publish(msg_str)
            
            self.get_logger().info(f"【Joyボタン検知】 /current_mode にパブリッシュしました: {self.current_mode}")

def main(args=None):
    rclpy.init(args=args)
    node = JoyController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
