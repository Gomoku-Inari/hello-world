import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import mediapipe as mp

class GestureController(Node):
    def __init__(self):
        super().__init__('gesture_controller')
        
        self.bridge = CvBridge()
        self.current_mode = "gray"

        # MediaPipeの初期化
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

        # 生カメラ映像を購読
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        
        # 🌟 追加：現在のモードを自分自身でも購読して「記憶を同期」させる
        self.mode_subscription = self.create_subscription(
            String, '/current_mode', self.mode_sync_callback, 10)
        
        # モードを配信するパブリッシャ
        self.mode_publisher = self.create_publisher(String, '/current_mode', 10)
        
        self.get_logger().info("ジェスチャー制御ノード（同期版）が起動しました。")

    # 🌟 追加：誰かがモードを変えたら、自分の変数も最新に上書きする
    def mode_sync_callback(self, msg):
        self.current_mode = msg.data

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)

        new_mode = self.current_mode

        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # 0番目の要素を指定してlabelを取得
                hand_label = results.multi_handedness[idx].classification[0].label
                
                # 指の先端ID（4, 8, 12, 16, 20）
                tips_ids = [4, 8, 12, 16, 20]
                fingers = []

                # 4本の指のY軸判定
                for id in tips_ids[1:]:
                    if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                # 親指のX軸判定（0番目の要素を指定）
                if hand_label == "Right":
                    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                else:
                    if hand_landmarks.landmark[tips_ids[0]].x > hand_landmarks.landmark[tips_ids[0] - 1].x:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                finger_count = sum(fingers)

                # 指の本数を画像モードに翻訳
                if finger_count == 1:
                    new_mode = "gray"
                elif finger_count == 2:
                    new_mode = "color"
                elif finger_count == 5:
                    new_mode = "face"

        # 記憶が同期されているため、ここのエッジ判定が常に正しく動きます
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            
            msg_str = String()
            msg_str.data = self.current_mode
            self.mode_publisher.publish(msg_str)
            
            self.get_logger().info(f"【ジェスチャー検知】 /current_mode にパブリッシュしました: {self.current_mode}")

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
