import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class ImageProcessor(Node):
    def __init__(self):
        super().__init__('image_processor')
        # /image_raw という名前のカメラ画像（トピック）を受け取る設定
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        
        # /image_gray という名前で白黒画像を配信する設定
        self.publisher = self.create_publisher(Image, '/image_gray', 10)
        
        # ROSとOpenCVを仲介するBridgeの初期化
        self.bridge = CvBridge()

    def image_callback(self, msg):
        # ROSの画像メッセージを、OpenCVのMat型（NumPy配列）に変換
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # グレースケール（白黒）に変換
        gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # OpenCVの画像を、再びROSの画像メッセージに変換して配信
        ros_image = self.bridge.cv2_to_imgmsg(gray_image, encoding='mono8')
        self.publisher.publish(ros_image)

def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
