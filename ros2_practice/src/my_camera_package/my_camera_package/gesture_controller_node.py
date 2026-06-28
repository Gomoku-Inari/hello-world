import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
from .mode_state_machine import ModeStateMachine  # 🌟 状態マシンをインポート

class GestureController(Node):
    def __init__(self):
        super().__init__('gesture_controller')
        
        self.bridge = CvBridge()
        self.mode_publisher = self.create_publisher(String, '/current_mode', 10)

        # 🌟 自身のパブリッシュ関数をコールバックとして状態マシンに「教育」して内包
        self.state_machine = ModeStateMachine(
            on_mode_changed_callback=self._publish_mode
        )

        # MediaPipeの初期化
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

        # 生カメラ映像を購読
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        
        # 現在のモードを自分自身でも購読して「記憶を同期」させる
        self.mode_subscription = self.create_subscription(
            String, '/current_mode', self.mode_sync_callback, 10)
        
        self.get_logger().info("ジェスチャー制御ノード（コールバックインジェクション版）が起動しました。")

    def _publish_mode(self, mode_str: str):
        """状態マシンからエッジ検知時に自動で呼び出されるパブリッシュの実体"""
        msg = String(data=mode_str)
        self.mode_publisher.publish(msg)
        self.get_logger().info(f"【状態変化】 /current_mode にパブリッシュしました: {mode_str}")

    def mode_sync_callback(self, msg):
        # 他ノードの変更を状態マシンに同期（コールバックは走らない）
        self.state_machine.sync_mode(msg.data)

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)

        # 判定前のデフォルト値として、現在の状態を取得しておく
        target_mode = self.state_machine.current_mode

        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
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

                # 親指のX軸判定
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
                    target_mode = "gray"
                elif finger_count == 2:
                    target_mode = "color"
                elif finger_count == 5:
                    target_mode = "face"

        # 🌟 ノード側は判定を見て「ただ設定を要求するだけ」の共通ルールに従う！
        # 状態が変わっていた時だけ、内部で _publish_mode が自動発火します。
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
