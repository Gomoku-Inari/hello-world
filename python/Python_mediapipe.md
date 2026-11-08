# PythonでAIカメラを作ってみよう

## カメラの映像を画面に出してみよう。

### 1. Python 3.11 のインストール確認

Windowsでは複数のバージョンを共存させることが多いため、まずはPython 3.11がインストールされているか（あるいはランチャー経由で呼び出せるか）を確認します。
VS Codeのターミナル（PowerShell）を開き、以下を実行してください。
```powershell
py -3.11 --version
```
コードは注意してご使用ください。
※ Python 3.11.x と返ってくればOKです。もし入っていない場合は、Python公式サイトから Windows installer (64-bit) の 3.11系の最新（例: 3.11.9など）をインストールしてください。

### 2. 仮想環境（venv）の作成とアクティベート

ここがWindows（PowerShell）で一番つまずきやすいポイントです。

#### 2-1. スクリプト実行の許可（Windows特有の儀式）

Windowsの初期設定では、セキュリティ制限により仮想環境を有効化するスクリプト（.ps1）の実行が禁止されています。これを現在のセッション（ターミナルを閉じるまで）のみ許可します。

``` powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
```
コードは注意してご使用ください。
(ハンズオン当日、若手メンバーのPCでほぼ確実に発生するエラーなので、テキストに含めておくことを強くおすすめします)

#### 2-2. 仮想環境の作成

作業フォルダ（例: python-practice）に移動し、Python 3.11を指定して仮想環境を作ります。
``` powershell
py -3.11 -m venv .venv
```
コードは注意してご使用ください。

#### 2-3. 仮想環境のアクティベート

Linuxの source ではなく、スクリプトを直接叩きます。
``` powershell
.venv\Scripts\Activate.ps1
```
コードは注意してご使用ください。
ターミナルの行頭に (.venv) と表示されれば成功です。

### 3. ライブラリのインストール

OpenCVをインストールします。MediaPipeも見据えて、まずはOpenCVだけで進めます。
``` powershell
pip install opencv-python
```
コードは注意してご使用ください。

### 4. OpenCVでカメラを開く最小コード

作業フォルダに camera_test.py というファイルを作成し、以下のコードを貼り付けてください。
```python

import cv2

def main():
    # カメラのオープン (0は内蔵カメラ、外付けがある場合は1や2を試す)
    # Windowsでは DirectShow (cv2.CAP_DSHOW) を指定すると起動が速くなります
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    print("カメラを起動しました。'q' キーを押すと終了します。")

    while True:
        # 1フレームキャプチャ
        ret, frame = cap.read()
        if not ret:
            print("エラー: フレームを取得できませんでした。")
            break

        # 画面に表示
        cv2.imshow("Handson - Camera Test", frame)

        # 1ms待機し、'q' キーが押されたらループを抜ける
        # 組み込みエンジニアにお馴染みのポーリング処理
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 後処理（リソース解放）
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```
コードは注意してご使用ください。

💡 組み込み視点でのTips（受講生への解説ポイント）

• cv2.CAP_DSHOW: Windows環境において、カメラのキャプチャをDirectShow経由で行うフラグです。これを入れないと、Windowsではカメラが起動するまでに5〜10秒ほどフリーズする（タイムアウトを待つような挙動になる）トラブルが頻発します。
• cv2.waitKey(1): 描画処理のためのイベントループを回す役割も兼ねています。これがないと imshow のウィンドウがフリーズして真っ白になります。

### 5. 実行

VS Codeのターミナルから実行します。
``` powershell
python camera_test.py
```
コードは注意してご使用ください。
無事に別ウィンドウでカメラ映像が表示され、q キーで綺麗に終了できれば、WindowsでのOpenCV環境は完全にクリアです！
まずはご自身のPCで カメラ映像が無事に表示されるか 試してみますか？
問題なく動くことが確認できたら、次はステップ2の 「MediaPipe（顔検出）を組み込む手順とコード」 へ進みましょう！


## MediaPipeでの顔検出

``` python
import cv2
import mediapipe as mp

def main():
    # MediaPipeの顔検出モジュールの初期化 (旧Solutions API)
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils  # 枠や点を描画する便利ツール

    # カメラのオープン
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    # 顔検出モデルの読み込み（信頼度のしきい値を0.5に設定）
    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        print("MediaPipe 起動。'q' キーで終了します。")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 組み込み解説ポイント①: OpenCVはBGR、MediaPipeはRGBなので変換が必要
            # 変換を忘れると、顔の認識率が大幅に低下します
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # AIによる推論実行
            results = face_detection.process(rgb_frame)

            # 検出結果がある場合、画面に枠と特徴点を描画
            if results.detections:
                for detection in results.detections:
                    # MediaPipeが用意してくれている標準の描画機能でカメラ映像に上書き
                    mp_drawing.draw_detection(frame, detection)

            # 画面表示
            cv2.imshow("Handson - MediaPipe Face Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```
