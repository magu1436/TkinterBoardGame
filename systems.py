


class BGSystemException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Player:
    """プレイヤーを表すクラス"""
    def __init__(self, name: str | None = None):
        self.name = name