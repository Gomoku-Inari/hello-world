import cv2
import mediapipe as mp

def main():
    # 1. MediaPipeの手検出セットアップ
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    # 2. PCのWebカメラを直接オープン
    cap = cv2.VideoCapture(0)

    print("単体テストを開始します。カメラに向かって手をかざしてください。[q]キーで終了します。")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # MediaPipe用に画像をRGBに変換
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        finger_count = 0

        # 手が検出された場合の処理
        if results.multi_hand_landmarks:
            # 🌟 enumerateを使ってループのインデックス(idx)を正確に取得
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # 画面に手の骨格線を描画
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # 検出された手が「右手」か「左手」かのラベルを取得
                hand_label = results.multi_handedness[idx].classification[0].label # 'Left' または 'Right'

                # 🌟 正しい指の先端のID定義（4:親指、8:人差し指、12:中指、16:薬指、20:小指）
                tips_ids = [4, 8, 12, 16, 20]
                fingers = []

                # 4本の指（人差し指〜小指）のY軸判定
                for id in tips_ids[1:]:
                    if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                # 親指のX軸判定（左右でロジックを反転）
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

                # 立っている指の合計本数
                finger_count = sum(fingers)

        # 画面に指の本数と、認識した手の左右をリアルタイム描画
        cv2.putText(frame, f'Fingers: {finger_count}', (30, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

        cv2.imshow('Gesture Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
