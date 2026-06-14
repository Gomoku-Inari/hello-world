from abc import ABC, abstractmethod

class ModeResolverInterface(ABC):
    @abstractmethod
    def resolve_mode(self, msg) -> str:
        """ 
        受け取ったメッセージから画像処理モードを決定して返す仕様（契約）
        """
        pass
