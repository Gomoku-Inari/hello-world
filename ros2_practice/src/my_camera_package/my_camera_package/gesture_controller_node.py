import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
from .mode_state_machine import ModeStateMachine
from .yolo_finger_detector import YOLOFingerDetector


class GestureController(Node):
    def __init__(self):
        super().__init__('gesture_controller')

        self.bridge = CvBridge()
        self.mode_publisher = self.create_publisher(String, '/current_mode', 10)
        self.state_machine = ModeStateMachine(
            on_mode_changed_callback=self._publish_mode
        )
        self.detector = YOLOFingerDetector(model_path='yolov8n.pt', confidence=0.25)

        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)

        self.mode_subscription = self.create_subscription(
            String, '/current_mode', self.mode_sync_callback, 10)

        self.get_logger().info("YOLO ベースのジェスチャー制御ノードが起動しました。")

    def _publish_mode(self, mode_str: str):
        msg = String(data=mode_str)
        self.mode_publisher.publish(msg)
        self.get_logger().info(f"【状態変化】 /current_mode にパブリッシュしました: {mode_str}")

    def mode_sync_callback(self, msg):
        self.state_machine.sync_mode(msg.data)

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        target_mode = self.state_machine.current_mode

        try:
            finger_count = self.detector.detect_finger_count(cv_image)
        except Exception as exc:
            self.get_logger().warning(f"YOLO finger detection failed: {exc}")
            return

        if finger_count == 1:
            target_mode = 'gray'
        elif finger_count == 2:
            target_mode = 'color'
        elif finger_count == 3:
            target_mode = 'BIOLOGICAL'
        elif finger_count == 5:
            target_mode = 'face'

        self.state_machine.set_mode(target_mode)


def main(args=None):
    rclpy.init(args=args)
    node = GestureController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
