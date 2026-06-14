import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy  # ゲームパッド用のメッセージ型

class JoyTestNode(Node):
    def __init__(self):
        super().__init__('joy_test_node')
        
        # 🌟 /joy トピックを受け取るサブスクライバを作成
        self.subscription = self.create_subscription(
            Joy, '/joy', self.joy_callback, 10)
        
        self.get_logger().info("Joy単体テストノードが起動しました。ボタンを押してください。")

    def joy_callback(self, msg):
        # コントローラーのボタンが押されたらここが自動で実行されます
        
        # 🌟 まずは、配列(buttons)の何番目が「1」になっているか探してログに出す
        for index, status in enumerate(msg.buttons):
            if status == 1:
                self.get_logger().info(f"【検知】 ボタン番号 [ {index} ] が押されました！")

def main(args=None):
    rclpy.init(args=args)
    node = JoyTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
