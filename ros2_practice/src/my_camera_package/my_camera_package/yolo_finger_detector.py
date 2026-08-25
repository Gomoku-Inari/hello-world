"""YOLOベースの指検出用ユーティリティ。

MediaPipeのランドマーク計算を置き換えるために、YOLOのラベル群を指の本数へ変換する
変換層です。実際の学習済みモデルは以下のようなクラス名を返す前提です。

- one, two, three, four, five
- finger_1, finger_2, ..., finger_5
- open_hand, closed_hand

この変換層は、YOLOの出力をROSノードに吸収させるための安全な入口として使います。
"""

from __future__ import annotations


def _normalize_label(label) -> str:
    return str(label).strip().lower().replace(" ", "_")


def resolve_finger_count_from_labels(labels):
    """YOLOのラベルリストから指の本数を推定する。

    例:
      ['one'] -> 1
      ['right_hand', 'two'] -> 2
      ['finger_5'] -> 5
    """
    if not labels:
        return 0

    normalized = [_normalize_label(label) for label in labels]

    mapping = {
        "one": 1,
        "1": 1,
        "finger_1": 1,
        "finger1": 1,
        "two": 2,
        "2": 2,
        "finger_2": 2,
        "finger2": 2,
        "three": 3,
        "3": 3,
        "finger_3": 3,
        "finger3": 3,
        "four": 4,
        "4": 4,
        "finger_4": 4,
        "finger4": 4,
        "five": 5,
        "5": 5,
        "finger_5": 5,
        "finger5": 5,
        "open_hand": 5,
        "five_fingers": 5,
        "all_fingers": 5,
    }

    detected_counts = []
    for label in normalized:
        if label in mapping:
            detected_counts.append(mapping[label])
            continue

        for key, value in mapping.items():
            if key in label and "finger" in label:
                detected_counts.append(value)
                break

    if detected_counts:
        return max(detected_counts)

    return 0


class YOLOFingerDetector:
    """学習済みYOLOモデルを使って、指の本数を推定するラッパー。"""

    def __init__(self, model_path="yolov8n.pt", confidence=0.25, device='cpu'):
        self.model_path = model_path
        self.confidence = confidence
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
        except Exception:
            return None

        self.model = YOLO(self.model_path)
        try:
            self.model.to(self.device)
        except Exception as exc:
            if self.device == 'npu':
                print(f"Warning: NPU initialization failed: {exc}")
                print("OpenVINO tools may need to be installed:")
                print("  pip install openvino openvino-dev")
                print("Falling back to CPU...")
                self.model.to('cpu')
            else:
                pass
        return self.model

    def set_device(self, device):
        """実行時にデバイスを切り替える。
        
        Args:
            device: 'cpu', 0 (GPU), 1 (GPU2), etc.
        """
        self.device = device
        if self.model:
            try:
                self.model.to(device)
            except Exception:
                pass

    def _extract_labels(self, results):
        if results is None:
            return []

        labels = []

        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or item.get("class_name")
                    if label:
                        labels.append(_normalize_label(label))
                elif hasattr(item, "boxes"):
                    names = getattr(item, "names", {}) or {}
                    cls_list = getattr(item.boxes, "cls", None)
                    if cls_list is not None:
                        try:
                            class_ids = cls_list.cpu().numpy().astype(int).tolist()
                            for class_id in class_ids:
                                labels.append(_normalize_label(names.get(class_id, class_id)))
                        except Exception:
                            pass
            return labels

        try:
            if hasattr(results, "boxes"):
                names = getattr(results, "names", {}) or {}
                cls_list = getattr(results.boxes, "cls", None)
                if cls_list is not None:
                    class_ids = cls_list.cpu().numpy().astype(int).tolist()
                    for class_id in class_ids:
                        labels.append(_normalize_label(names.get(class_id, class_id)))
        except Exception:
            pass

        return labels

    def detect_finger_count(self, frame):
        """OpenCVのBGR画像を受け取り、指の枚数を返す。"""
        if self.model is None:
            return 0

        results = self.model(frame, conf=self.confidence, verbose=False)
        labels = self._extract_labels(results)
        return resolve_finger_count_from_labels(labels)
