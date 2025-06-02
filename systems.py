from __future__ import annotations

from typing import TYPE_CHECKING
from tkinter import Event

if TYPE_CHECKING:
    if __name__ == "__main__":
        from objects import Piece, Tile
        from board import Board
        from utilities import Coordinate
    else:
        from .objects import Piece, Tile
        from .board import Board
        from .utilities import Coordinate

class BGSystemException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Player:
    """プレイヤーを表すクラス"""
    def __init__(self, name: str | None = None):
        self.name = name


class BGEvent:
    """PieceやTileオブジェクトがクリックされたときに呼び出される関数の引数として渡されるイベントオブジェクトクラス.
    
    Attributes:
        board(Board): クリックされたオブジェクトが存在するボード
        target_obj(Piece | Tile): クリックされたオブジェクト
        coordinate(Coordinate): クリックされたマスの座標
        tkevent(tkinter.Event): tkinterのクリックイベントが渡すEventオブジェクト"""

    def __init__(self, board: Board, target_obj: Piece | Tile, coordinate: Coordinate, tkevent: Event) -> None:
        """コンストラクタ"""
        self.board: Board = board
        self.target_obj: Piece | Tile = target_obj
        self.coordinate: Coordinate = coordinate
        self.tkevent: Event = tkevent