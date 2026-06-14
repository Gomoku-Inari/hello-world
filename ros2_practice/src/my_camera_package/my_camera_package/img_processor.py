import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, Joy
from cv_bridge import CvBridge
import cv2

# 🌟 分割したファイルから必要な仕様と実装をインポート
from .interfaces import ModeResolverInterface
from .joy_resolver import JoyModeResolver

class ImageProcessor(Node):
    def __init__(self, resolver: ModeResolverInterface):
        super().__init__('image_processor')
        
        self.resolver = resolver
        self.current_mode = "gray"
        
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.publisher = self.create_publisher(Image, '/image_gray', 10)
        
        # ゲームパッドトピックの購読
        self.joy_subscription = self.create_subscription(
            Joy, '/joy', self.control_callback, 10)
        
        self.bridge = CvBridge()

    def control_callback(self, msg):
        self.current_mode = self.resolver.resolve_mode(msg)
        self.get_logger().info(f"現在の処理モード: {self.current_mode}")

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        if self.current_mode == "gray":
            processed_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            encoding = 'mono8'
        elif self.current_mode == "face":
            processed_image = cv_image.copy()
            cv2.rectangle(processed_image, (220, 140), (420, 340), (0, 0, 255), 3)
            encoding = 'bgr8'
        else:
            processed_image = cv_image
            encoding = 'bgr8'

        ros_image = self.bridge.cv2_to_imgmsg(processed_image, encoding=encoding)
        self.publisher.publish(ros_image)


def main(args=None):
    rclpy.init(args=args)
    
    # 🌟 依存性の注入（DI）
    resolver = JoyModeResolver()
    node = ImageProcessor(resolver)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
