import cv2
import sys
from .yolo_finger_detector import YOLOFingerDetector


def main():
    # コマンドライン引数でデバイスを指定: python -m my_camera_package.gesture_test cpu|0|npu
    device = sys.argv[1] if len(sys.argv) > 1 else 'cpu'
    print(f"\n=== YOLO 指検出テスト（デバイス: {device}）===")
    print("[q]キーで終了\n")
    
    # NPU用の初期化ヒント
    if device == 'npu':
        print("💡 Intel Core Ultra NPU を使用しています。")
        print("   OpenVINO がインストールされていることを確認してください:")
        print("   pip install openvino openvino-dev\n")
    
    detector = YOLOFingerDetector(model_path='yolov8n.pt', confidence=0.25, device=device)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: カメラを開けません。")
        return

    print("YOLO 指検出テストを開始します。カメラに向かって手をかざしてください。")

    frame_count = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1

        try:
            finger_count = detector.detect_finger_count(frame)
        except Exception as exc:
            print(f"YOLO detection failed: {exc}")
            finger_count = 0

        # デバッグ用：検出結果を標準出力に出す（30フレームごと）
        if frame_count % 30 == 0:
            try:
                from ultralytics import YOLO
                if detector.model:
                    results = detector.model(frame, conf=detector.confidence, verbose=False)
                    if results:
                        result = results[0]
                        detected_classes = []
                        if hasattr(result, 'boxes') and result.boxes is not None:
                            names = result.names or {}
                            cls_list = result.boxes.cls
                            if cls_list is not None:
                                class_ids = cls_list.cpu().numpy().astype(int).tolist() if hasattr(cls_list, 'cpu') else cls_list
                                detected_classes = [names.get(int(cid), str(cid)) for cid in class_ids]
                        print(f"[Frame {frame_count}] Device: {detector.device}, Detected: {detected_classes}, Fingers: {finger_count}")
            except Exception as debug_exc:
                pass

        cv2.putText(frame, f'Fingers: {finger_count}', (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

        cv2.imshow('Gesture Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
