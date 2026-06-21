import cv2
import mediapipe as mp
from .interfaces import ModeResolverInterface

class GestureModeResolver(ModeResolverInterface):
    def __init__(self, current_mode="gray"):
        self._current_mode = current_mode
        
        # MediaPipeの初期化（ノード起動時に1度だけ実行されて使い回されるので高効率）
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    def resolve_mode(self, msg_frame) -> str:
        """
        ROS 2の画像メッセージから変換された「OpenCVの生フレーム」を受け取り、
        指の本数を解析して、次のモードを決定して返す。
        """
        # MediaPipe用にRGBへ変換
        image_rgb = cv2.cvtColor(msg_frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)

        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_label = results.multi_handedness[idx].classification[0].label
                
                # 指の先端ID（4:親指、8:人差し指、12:中指、16:薬指、20:小指）
                tips_ids = [4, 8, 12, 16, 20]
                fingers = []

                # 4本の指（人差し指〜小指）のY軸判定
                for id in tips_ids[1:]:
                    if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                # 親指のX軸判定（左右でロジック反転）
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

                # 🌟 指の本数に応じたモード決定（仕様の具現化）
                if finger_count == 1:
                    self._current_mode = "gray"
                elif finger_count == 2:
                    self._current_mode = "color"
                elif finger_count == 5:
                    self._current_mode = "face"

        return self._current_mode
