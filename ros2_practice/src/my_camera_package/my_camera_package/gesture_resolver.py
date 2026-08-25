import cv2
from .interfaces import ModeResolverInterface
from .yolo_finger_detector import YOLOFingerDetector


class GestureModeResolver(ModeResolverInterface):
    def __init__(self, current_mode="gray", model_path="yolov8n.pt", confidence=0.25):
        self._current_mode = current_mode
        self.detector = YOLOFingerDetector(model_path=model_path, confidence=confidence)

    def resolve_mode(self, msg_frame) -> str:
        """
        ROS 2の画像メッセージから変換された「OpenCVの生フレーム」を受け取り、
        YOLOの検出結果から指の本数を解析して、次のモードを決定して返す。
        """
        try:
            finger_count = self.detector.detect_finger_count(msg_frame)
        except Exception:
            return self._current_mode

        if finger_count == 1:
            self._current_mode = "gray"
        elif finger_count == 2:
            self._current_mode = "color"
        elif finger_count == 5:
            self._current_mode = "face"

        return self._current_mode
