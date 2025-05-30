from __future__ import annotations

from typing import Callable, TYPE_CHECKING
from copy import deepcopy, copy
from abc import ABC

import tkinter
from tkinter import PhotoImage

if __name__ == "__main__":
    from imagetools import BoardGamePhotoImage, PathOrImage
    from utilities import Coordinate, Coordinatelike, CoordinateValue
    from systems import Player, BGEvent
else:
    from .imagetools import BoardGamePhotoImage, PathOrImage
    from .utilities import Coordinate, Coordinatelike, CoordinateValue
    from .systems import Player, BGEvent

if TYPE_CHECKING:
    if __name__ == "__main__":
        from board import Board
    else:
        from .board import Board


class BGObjectsException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class NotAssignedCoordinateError(BGObjectsException):
    """座標が指定されていない場合に生じる.
    """
    def __str__(self):
        return f"a coordinate is not assigned"


class CloneMixin:
    """
    この mixin を継承しておくと、 .clone() が使えるようになります。
    """
    def clone(self):
        # 1) 浅いコピーを作成（型も __dict__ のキーもそのまま）
        new = copy(self)
        # 2) 各属性を適切に複製して再セット
        for name, val in self.__dict__.items():
            # 自分で copy() を持っていれば再帰呼び出し
            if hasattr(val, "copy") and callable(val.copy):
                new_val = val.copy()
            # 自分で clone() を持っていれば再帰呼び出し
            elif hasattr(val, "clone") and callable(val.clone):
                new_val = val.clone()
            else:
                # それ以外は deepcopy を試みる
                try:
                    new_val = deepcopy(val)
                except Exception:
                    # deepcopy 不可なら元のオブジェクトを流用
                    new_val = val
            setattr(new, name, new_val)
        return new


class BoardGameVisualObject(ABC, CloneMixin):
    """
    ボードゲームの視覚的なオブジェクトを表すクラス
    """

    def __init__(
            self, 
            image: PathOrImage | None = None,
            image_display_size: Coordinatelike | None = None,
            right_clicked_func: Callable[[BGEvent], None] | None = None,
            center_clicked_func: Callable[[BGEvent], None] | None = None,
            left_clicked_func: Callable[[BGEvent], None] | None = None,
            right_release_func: Callable[[BGEvent], None] | None = None,
            center_release_func: Callable[[BGEvent], None] | None = None,
            left_release_func: Callable[[BGEvent], None] | None = None,
            ):
        self.image = BoardGamePhotoImage(image)
        self.right_clicked_func: Callable[[BGEvent], None] | None = right_clicked_func
        self.center_clicked_func: Callable[[BGEvent], None] | None = center_clicked_func
        self.left_clicked_func: Callable[[BGEvent], None] | None = left_clicked_func
        self.right_release_func: Callable[[BGEvent], None] | None = right_release_func
        self.center_release_func: Callable[[BGEvent], None] | None = center_release_func
        self.left_release_func: Callable[[BGEvent], None] | None = left_release_func
        self._id: int | None = None    # Canvas上にあるときのid. idがないとき、このオブジェクトはキャンバス上にない
    
    @property
    def image_display_size(self) -> Coordinate:
        return Coordinate(self.image.width(), self.image.height())


    def set_image(self, image: BoardGamePhotoImage | PhotoImage | str | None, display_size: Coordinatelike | None = None) -> None:
        """画像を設定する.

        `display_size` が `None` でかつ既に画像を保持している場合、
        新しい画像は自動で既存の画像のサイズにリサイズされる

        Args:
            image (BoardGamePhotoImage | PhotoImage | str | None): 画像
            size (Coordinatelike | None, optional): 画像のサイズ. defaults to None.
        """
        if display_size is None:
            display_size = self.image_display_size
        self.image = BoardGamePhotoImage(image, display_size)
    
    def on_click(self, board: Board, target_obj: Piece | Tile, coordinate: Coordinate, tkevent: tkinter.Event) -> bool:
        """自身がクリックされたときに呼び出される関数

        `*_clicked_func` が指定されている場合は, その関数を呼び出す.
        """
        event = BGEvent(board, target_obj, coordinate, tkevent)
        match tkevent.num:
            case 1:
                if self.left_clicked_func is not None:
                    self.left_clicked_func(event)
            case 2:
                if self.center_clicked_func is not None:
                    self.center_clicked_func(event)
            case 3:
                if self.right_clicked_func is not None:
                    self.right_clicked_func(event)
            case _: return False
        return True
    
    def on_release(self, board: Board, target_obj: Piece | Tile, coordinate: Coordinate, tkevent: tkinter.Event) -> bool:
        """自身がクリックされたときに呼び出される関数

        `*_release_func` が指定されている場合は, その関数を呼び出す.
        """
        event = BGEvent(board, target_obj, coordinate, tkevent)
        match tkevent.num:
            case 1:
                if self.left_release_func is not None:
                    self.left_release_func(event)
            case 2:
                if self.center_release_func is not None:
                    self.center_release_func(event)
            case 3:
                if self.right_release_func is not None:
                    self.right_release_func(event)
            case _: return False
        return True
    
    def __deepcopy__(self, memo):
        # 循環を防ぐためにすでにコピー済みならそれを返す
        if id(self) in memo:
            return memo[id(self)]

        new = self.clone()

        # 循環を防ぐために memo に登録しておく
        memo[id(self)] = new

        return new


class Piece(BoardGameVisualObject):

    def __init__(
            self,
            image: PathOrImage | None = None,
            image_display_size: Coordinatelike | None = None,
            auto_resize: bool = True,
            owner: Player | None = None,
            right_clicked_func: Callable[[BGEvent], None] | None = None,
            center_clicked_func: Callable[[BGEvent], None] | None = None,
            left_clicked_func: Callable[[BGEvent], None] | None = None,
            right_release_func: Callable[[BGEvent], None] | None = None,
            center_release_func: Callable[[BGEvent], None] | None = None,
            left_release_func: Callable[[BGEvent], None] | None = None,
            ):
        """
        コンストラクタ

        `auto_resize` が `True` の場合, ボードに置いた際に自動でリサイズする.

        Args:
            image (BoardGamePhotoImage | PhotoImage | str): 画像
            image_display_size (Coordinatelike | None, optional): 画像のサイズ. defaults to None.
            auto_resize (bool, optional): 画像のサイズを自動調整するかどうか. defaults to True.
            button_func (Callable | None, optional): ボタンの関数. defaults to None.
        """
        self._coordinate: Coordinate | None = None
        self.auto_resize: bool = auto_resize
        self.owner: Player | None = owner
        super().__init__(image, image_display_size, 
                         right_clicked_func, center_clicked_func, left_clicked_func,
                         right_release_func, center_release_func, left_release_func)

    @property
    def coordinate(self) -> Coordinate | None:
        return deepcopy(self._coordinate)
    
    @property
    def x(self) -> CoordinateValue:
        if self.coordinate is None:
            raise NotAssignedCoordinateError()
        return self.coordinate.x
    
    @property
    def y(self) -> CoordinateValue:
        if self.coordinate is None:
            raise NotAssignedCoordinateError()
        return self.coordinate.y


class Tile(BoardGameVisualObject):
    
    def __init__(
            self, 
            image: PathOrImage | None = None,
            image_display_size: Coordinatelike | None = None,
            auto_resize: bool = True,
            right_clicked_func: Callable[[BGEvent], None] | None = None,
            center_clicked_func: Callable[[BGEvent], None] | None = None,
            left_clicked_func: Callable[[BGEvent], None] | None = None,
            right_release_func: Callable[[BGEvent], None] | None = None,
            center_release_func: Callable[[BGEvent], None] | None = None,
            left_release_func: Callable[[BGEvent], None] | None = None,
            ):
        """
        コンストラクタ
        Args:
            image (BoardGamePhotoImage | PhotoImage | None, optional): 画像. defaults to None.
            image_display_size (Coordinatelike | None, optional): 画像のサイズ. defaults to None.
            button_func (Callable | None, optional): ボタンの関数. defaults to None.
        """
        super().__init__(image, image_display_size, 
                         right_clicked_func, center_clicked_func, left_clicked_func,
                         right_release_func, center_release_func, left_release_func)
        self.auto_resize: bool = auto_resize