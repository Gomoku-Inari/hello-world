# my_camera_package

ゲームパッド（コントローラー）およびカメラからのジェスチャー認識（指の本数カウント）によって、画像処理モードをリアルタイムに切り替えることができる、ROS 2 Jazzy対応の高度なHMI（ヒューマンマシンインターフェース）パッケージです。

## 🎯 本パッケージの設計思想と特徴

1. **完全な疎結合・分散型アーキテクチャ**
   画像加工を行うノード（`img_processor`）から入力デバイスの依存関係を完全に排除。`/current_mode` という通信トピックを明確な「デバッグ・通信界面」として定義し、プロセス単位でノードを完全分離しています。
2. **エッジでの重複送信の抑止（エッジトリガー制御）**
   各制御ノード（Joy / ジェスチャー）は、人間の操作やAIの判定に変化があった「状態変化の瞬間」だけトピックをパブリッシュします。これにより、無駄なトラフィックと受信側の割り込みCPU負荷を最小限に抑えています。
3. **マルチ入力における状態の完全同期**
   各制御ノードは、自分自身でも `/current_mode` トピックをサブスクライブしてシステム全体の最新状態を常に共有しています。これにより、ゲームパッドとジェスチャーのどちらから交互に操作しても、エッジ判定が衝突せず100%リアルタイムに追従します。また、将来的なスマホアプリ等からの割り込み送信にも標準で対応可能です。

## 📂 ファイル構成と役割分担

```text
my_camera_package/
├── launch/
│   └── camera_system.launch.py   # 全ノード（カメラ・Joy・各種コントローラー・本体・モニター）の一括統合起動
├── my_camera_package/
│   ├── __init__.py
│   ├── img_processor.py          # 🤖 画像加工ノード（指示されたモードを待って画像を処理するだけ）
│   ├── gesture_controller_node.py# 🖐️ ジェスチャー制御ノード（MediaPipe内蔵、状態変化時のみ送信）
│   └── joy_controller_node.py    # 🎮 ゲームパッド制御ノード（Joyの入力を短い文字列に翻訳、状態変化時のみ送信）
├── package.xml
├── setup.cfg
└── setup.py
```

## 🛠️ 環境構築と前提条件

Ubuntu 24.04 (ROS 2 Jazzy) のシステム環境を汚さないよう、Pythonの仮想環境（VENV）にAIライブラリを隔離して構築します。

### 1. 必要となるROS 2標準パッケージのインストール
```bash
sudo apt update
sudo apt install ros-jazzy-joy ros-jazzy-v4l2-camera ros-jazzy-image-view
```

### 2. Python仮想環境（VENV）の作成とMediaPipeのインストール
ROS 2ワークスペースの直下に仮想環境を作成し、`solutions` APIが健在な安定バージョンのMediaPipeをインストールします。
```bash
# ワークスペースに移動
cd ~/hello_world/ros2_practice/

# 仮想環境「venv」の作成とアクティベート
python3 -m venv venv
source venv/bin/activate

# 安定版MediaPipeのインストール
pip install mediapipe==0.10.21
```

### 3. ROS 2ビルド先へのシンボリックリンク（紐付け）の作成
ROS 2のプロセスが、隔離された仮想環境内のMediaPipeを正しく発見できるように、ビルド先（site-packages）へショートカットを直接作成します。
```bash
# 事前に一度クリーンビルドを実行
cd ~/hello_world/ros2_practice
rm -rf build/ install/ log/
colcon build

# 仮想環境のライブラリへのシンボリックリンクを作成 (1行ずつ実行)
ln -s ~/hello_world/ros2_practice/venv/lib/python3.12/site-packages/mediapipe ~/hello_world/ros2_practice/install/my_camera_package/lib/python3.12/site-packages/
ln -s ~/hello_world/ros2_practice/venv/lib/python3.12/site-packages/google ~/hello_world/ros2_practice/install/my_camera_package/lib/python3.12/site-packages/
```

## 🚀 実行方法

環境を読み込み、Launchファイルで一括起動します。

```bash
# 1. 仮想環境とROS環境の二重読み込み
source ~/hello_world/ros2_practice/venv/bin/activate
source ~/hello_world/ros2_practice/install/setup.bash

# 2. Launchファイルによる一発起動！
ros2 launch my_camera_package camera_system.launch.py
```

## 🎮 操作方法と対応モード

以下のどちらのデバイスから操作しても、相互に干渉することなくリアルタイムにモニターの映像モードが切り替わります。

### 🖐️ ジェスチャー認識（カメラに向かって手をかざす）
- **指を 1 本立てる** ➔ **グレースケール（白黒）モード** に変更
- **指を 2 本立てる（ピース）** ➔ **カラー（無加工）モード** に変更
- **指を 5 本立てる（パー）** ➔ **顔検出枠（デモ用の赤い四角形）モード** に変更

### 🎮 ゲームパッド（コントローラー）
- **0 番ボタン（多くのパッドでAボタン）** ➔ **グレースケールモード** に変更
- **1 番ボタン（多くのパッドでBボタン）** ➔ **カラーモード** に変更
- **2 番ボタン（多くのパッドでXボタン）** ➔ **顔検出枠モード** に変更
