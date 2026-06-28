from typing import Callable

class ModeStateMachine:
    """
    ROS 2の世界から隔離されつつも、通知の主導権を握る状態管理クラス。
    コンストラクタで「モードが変わった時の通知方法（コールバック）」を受け取ります。
    """
    def __init__(self, on_mode_changed_callback: Callable[[str], None], initial_mode="gray"):
        self._current_mode = initial_mode
        # 🌟「モードを設定する＝世の中に通知する」というルールをここに登録
        self._on_mode_changed = on_mode_changed_callback

    @property
    def current_mode(self) -> str:
        return self._current_mode

    def sync_mode(self, external_mode: str):
        """他人が変えた状態への同期（ここではコールバックは呼ばない）"""
        self._current_mode = external_mode

    def set_mode(self, target_mode: str):
        """
        🌟 外部（Joyやジェスチャー）からモード設定を要求する唯一の界面。
        状態が変化した瞬間（エッジ）だけ、登録された通知処理を自動で実行します。
        """
        if target_mode != self._current_mode:
            self._current_mode = target_mode
            # 🌟 ルール化されたパブリッシュ（通知）を自動で裏側で呼び出す！
            self._on_mode_changed(self._current_mode)
