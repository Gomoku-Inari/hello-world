import rclpy
import os
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String  # 🌟 スマホや別ノードからの文字列を受け取るために追加！
from cv_bridge import CvBridge
import cv2
import numpy as np

class ImageProcessor(Node):
    def __init__(self):
        super().__init__('image_processor')
        
        # 初期モードは白黒
        self.current_mode = "gray"
        self.bridge = CvBridge()

        # 1. 映像ソースのサブスクライバとパブリッシャ
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.publisher = self.create_publisher(Image, '/image_gray', 10)
        
        # 🌟 2. 【recvMode界面】外部（指認識やスマホ）からのモード変更要求を待ち受ける
        self.mode_subscription = self.create_subscription(
            String, '/current_mode', self.mode_callback, 10)
        # 顔検出のための設定
        cascade_path = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    # Sigmoid関数
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    
    def biological_filter(self, image_gray, iterations=5, lmbda=0.15):
        """
        学生時代の「初期視覚・非線形数理モデル」を現代のNumPyで実装
        ※動画でリアルタイム（30fps）で動かすため、ループ回数(iterations)を5回に最適化しています
        """
        # 1. 計算精度を出すために0.0〜1.0の浮動小数点に変換
        U = image_gray.astype(np.float32) / 255.0
        U_original = U.copy()
    
        for _ in range(iterations):
            # 2. 上下左右のピクセルとの差分（エネルギーの元）を一瞬で計算
            # C言語のようなforループは一切不要。NumPyのスライス（ロール）で並列処理されます
            diff_u = np.roll(U, -1, axis=0) - U  # 下との差
            diff_d = np.roll(U, 1, axis=0) - U   # 上との差
            diff_r = np.roll(U, -1, axis=1) - U  # 右との差
            diff_l = np.roll(U, 1, axis=1) - U   # 左との差
        
            # 3. エネルギー関数の傾き（微分）を計算
            # データ項（元画像との解離を抑える）＋ 平滑化・エッジ項
            gradient = (U - U_original) + lmbda * (diff_u + diff_d + diff_r + diff_l)
        
            # 4. 金川先生からアドバイスを受けた tanh（ハイパボリックタンジェント）による非線形更新
            # これにより、ノイズが消えつつ、エッジ（輪郭）だけがシャープに残ります
            U = U - np.tanh(gradient) * 0.1
            # こちらはシグモイド関数
            # U = U - (self.sigmoid(gradient) - 0.5) * 0.1

            # 値が0.0〜1.0の範囲に収まるようにガード
            U = np.clip(U, 0, 1)

        # 5. 画面表示用に0〜255の8bit符号なし整数に戻す
        return (U * 255).astype(np.uint8)

    # 🌟 3. モード文字列が届いた時に動く関数（割り込み回数は激減しています）
    def mode_callback(self, msg):
        self.current_mode = msg.data
        self.get_logger().info(f"画像処理モードを切り替えました ➔ : {self.current_mode}")

    def image_callback(self, msg):
        # 外部の割り込みを気にせず、30fpsの画像処理に集中
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        if self.current_mode == "BIOLOGICAL": # 💫初期視覚の数理モデルによる数理モデル
            # 1. 一度グレースケール（白黒）にする
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            # 2. 自作の生体模倣フィルタを実行
            processed_image = self.biological_filter(gray)
            # 3. 表示用にBGRの3チャンネルに戻す
            cv_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)
            processed_image = cv_image
            encoding = "bgr8"
        elif self.current_mode == "gray":
            processed_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            encoding = 'mono8'
        elif self.current_mode == "face":
            processed_image = cv_image.copy()
            gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
            
            # 伝統のハール・カスケードで顔を検出（絶対にエラーになりません）
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # 見つかった顔を赤い四角で囲む
            for (x, y, w, h) in faces:
                cv2.rectangle(processed_image, (x, y), (x + w, y + h), (0, 0, 255), 3)

            encoding = 'bgr8'
        else:
            processed_image = cv_image
            encoding = 'bgr8'

        ros_image = self.bridge.cv2_to_imgmsg(processed_image, encoding=encoding)
        self.publisher.publish(ros_image)

def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor()  # 🌟 引数（Resolver）の注入が不要になり、完全に単体化！
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
