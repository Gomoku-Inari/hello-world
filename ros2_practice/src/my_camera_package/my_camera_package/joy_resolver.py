from sensor_msgs.msg import Joy
from .interfaces import ModeResolverInterface  # 🌟 仕様をインポート

class JoyModeResolver(ModeResolverInterface):
    def __init__(self, current_mode="gray"):
        self._current_mode = current_mode

    def resolve_mode(self, msg: Joy) -> str:
        # ゲームパッドのボタン判定ロジック
        if msg.buttons[0] == 1:
            self._current_mode = "gray"
        elif msg.buttons[1] == 1:
            self._current_mode = "color"
        elif msg.buttons[2] == 1:
            self._current_mode = "face"
            
        return self._current_mode
