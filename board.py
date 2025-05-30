from __future__ import annotations

from typing import Any
from copy import deepcopy

import tkinter
from tkinter import Canvas, Misc, Frame

if __name__ == "__main__":
    from imagetools import BoardGamePhotoImage, get_frame_width, PathOrImage
    from utilities import Coordinate, Coordinatelike
    from objects import Piece, Tile
else:
    from .imagetools import BoardGamePhotoImage, get_frame_width, PathOrImage
    from .utilities import Coordinate, Coordinatelike
    from .objects import Piece, Tile


# tags
BOARD_TAG = "board"
FRAME_TAG = "frame"
TILE_TAG = "tile"
PIECE_TAG = "piece"


class BoardGameException(Exception):
    """ボードゲームの例外クラス"""
    def __self__(self, *args, **kwards):
        self.args = args
        self.kwards = kwards

class LackOfSizeInfoError(BoardGameException):
    """サイズ情報が不足している場合に生じる.
    """
    def __str__(self):
        return f"lack of size to difine board-space size, needing to set either board_display_size or space_display_size"

class UndefinedBunttonFunctionError(BoardGameException):
    """ボタンの関数が指定されていない場合に生じる.
    """
    def __str__(self):
        return f"button function is not defined"

class InvalidSetCoordinateError(BoardGameException):
    """不適切な座標が設定されているオブジェクトの座標を取得しようとしたときに生じる.
    
    Args:
        obj(Piece): 不適切な座標が設定されているオブジェクト"""
    def __str__(self):
        obj: Piece = self.args[0]
        return f"Refered an invalid coordinate at {obj.coordinate}"



class Board(Frame):

    def __init__(
            self, 
            master: Misc,
            board_size: Coordinatelike, 
            background_image: PathOrImage,
            board_display_size: Coordinatelike,
            grid_image: PathOrImage | None = None,
            frame_image: PathOrImage | None = None,
            grid_display_width: int = 0,
            init_tile: Tile | None = None,
            **kwargs: Any
            ):
        """
        コンストラクタ
        Args:
            board_size (Coordinatelike): ボードのサイズ
        """

        self.__board_size: Coordinate = Coordinate(board_size)
        self.__whole_board_display_size: Coordinate = Coordinate(board_display_size)
        self.__board_id: int | None = None  # キャンバス上のボード画像のID
        self.__frame_id: int | None = None  # キャンバス上のボード画像のID

        frame_image = BoardGamePhotoImage(frame_image)
        self.__set_frame_info(frame_image)

        self.__set_board_sizes(board_display_size, grid_display_width)

        self.__board_image: BoardGamePhotoImage = self.__create_board_image(
            background_image,
            grid_image,
        )

        super().__init__(
            master, 
            width=self.__whole_board_display_size.x,
            height=self.__whole_board_display_size.y,
            **kwargs
            )
        
        self.board_canvas = Canvas(
            self, 
            width=self.__whole_board_display_size.x,
            height=self.__whole_board_display_size.y
            )
        self.board_canvas.bind("<ButtonPress>", self.on_click)
        self.board_canvas.bind("<ButtonRelease>", self.on_release)

        self.__board: list[list[None | Piece]] = [[None for _ in range(self.__board_size[0])] for _ in range(self.__board_size[1])]
        self.__tiles: list[list[Tile | None]] = [[None for _ in range(self.__board_size[0])] for _ in range(self.board_size[1])]
        self.__init_canvas(init_tile)
    
    @property
    def board_display_size(self) -> Coordinate:
        return deepcopy(self.__whole_board_display_size)
    
    @property
    def board_size(self) -> Coordinate:
        return deepcopy(self.__board_size)
    
    @property
    def board(self) -> list[list[Piece | None]]:
        return deepcopy(self.__board)
    
    @property
    def tiles(self) -> list[list[Tile | None]]:
        return deepcopy(self.__tiles)
    
    def __init_canvas(self, init_tile: Tile | None = None) -> None:
        self.__draw_board()
        self.__draw_frame()
        self.reset_tiles(init_tile)
        self.take_all_pieces()
        self.board_canvas.place(x=0, y=0)
    
    def __set_frame_info(self, frame_image: BoardGamePhotoImage):
        """フレーム画像の透過部分を参照してフレームの大きさを割り出し、セットする関数"""

        # ボードのサイズ比に合わせて、フレーム画像をリサイズ
        frame_image.resize(self.__whole_board_display_size)
        self.__frame_image: BoardGamePhotoImage = frame_image
        self.__frame_width: int = get_frame_width(self.__frame_image)
    
    def __set_board_sizes(
            self, 
            board_display_size: Coordinatelike | None, 
            grid_display_width: int, 
            ):
        """ボード関連の各種サイズを設定する

        Args:
            board_display_size (Coordinatelike): ボードのサイズ
            grid_display_width (int): グリッドの幅
        """
        board_display_size = Coordinate(board_display_size) - (self.__frame_width * 2, self.__frame_width * 2)
        space_display_size = Coordinate([(bds - grid_display_width * (bs - 1)) // bs for bds, bs in zip(board_display_size, self.__board_size)])
        self.__board_display_size: Coordinate = board_display_size
        self.__space_display_size: Coordinate = space_display_size
        self.__grid_display_width: int = grid_display_width

    def __create_board_image(self, 
            background_image: PathOrImage,
            grid_image: PathOrImage | None,
            ) -> BoardGamePhotoImage:
        """ボードの画像を作成する

        Args:
            background_image (PathOrImage): 背景画像
            grid_image (PathOrImage | None): グリッド画像
        Returns:
            BoardGamePhotoImage: ボードの画像
        """
        if not isinstance(background_image, BoardGamePhotoImage):
            background_image = BoardGamePhotoImage(background_image)
        if not isinstance(grid_image, BoardGamePhotoImage):
            grid_image = BoardGamePhotoImage(grid_image)
        
        # 下の画像を変更しないようにコピーを作成
        bg = background_image.copy()
        grid = grid_image.copy()

        # 画像のサイズをボードの大きさに合わせてリサイズ
        bg.resize(self.__board_display_size)
        if grid.height() < grid.width():    # 画像が縦長でなければ、回転して縦長にする.
            grid.rotate(90)
        grid.resize((self.__grid_display_width, self.__board_display_size.y))

        # グリッド画像をボード画像に配置
        for col in range(self.board_size[0]-1):
            x = self.__space_display_size.x + (self.__space_display_size.x + self.__grid_display_width) * col
            bg.put_on(grid, (x, 0))
        grid.rotate(90)
        grid.resize((self.__board_display_size.x, self.__grid_display_width))
        for row in range(self.board_size[1]-1):
            y = self.__space_display_size.y + (self.__space_display_size.y + self.__grid_display_width) * row
            bg.put_on(grid, (0, y))

        return BoardGamePhotoImage(bg)
    
    def get_tkcoor_from_board_coor(self, board_coordinate: Coordinatelike) -> Coordinate:
        """ボードの座標をtkinterの座標に変換する

        Args:
            coordinate (Coordinatelike): ボードの座標
        Returns:
            Coordinate: tkinterの座標
        """
        x, y = board_coordinate
        fx, fy = Coordinate(self.__frame_width, self.__frame_width)
        
        return Coordinate(
            x * (self.__space_display_size.x + self.__grid_display_width) + fx,
            y * (self.__space_display_size.y + self.__grid_display_width) + fy
        )

    def get_board_coor_from_tkcoor_in_board(self, tk_coordinate: Coordinatelike) -> Coordinate:
        """tkinterの座標をボードの座標に変換する

        Args:
            tk_coordinate (Coordinatelike): tkinterの座標
        Returns:
            Coordinate: ボードの座標
        """
        x, y = tk_coordinate
        fx, fy = Coordinate(self.__frame_width, self.__frame_width)
        
        return Coordinate(
            (x - fx) // (self.__space_display_size.x + self.__grid_display_width),
            (y - fy) // (self.__space_display_size.y + self.__grid_display_width)
        )

    def is_in_board(self, coordinate: Coordinatelike) -> bool:
        """座標がボードの中であるかどうか判定するメソッド
        
        Args:
            coordinate(Coordinatelike): ボードの内側であるか判定する座標"""
        coordinate = Coordinate(coordinate)
        if coordinate.x < 0 or self.board_size.x - 1 < coordinate.x:
            return False
        if coordinate.y < 0 or self.board_size.y - 1 < coordinate.y:
            return False
        return True

    def on_click(self, event: tkinter.Event) -> None:
        coor = self.get_board_coor_from_tkcoor_in_board((event.x, event.y))
        tile = self.get_tile(coor)
        if tile is not None:
            tile.on_click(self, tile, coor, event)
            return
        piece = self.get(coor)
        if piece is not None:
            piece.on_click(self, piece, coor, event)
            return
    
    def on_release(self, event: tkinter.Event) -> None:
        coor = self.get_board_coor_from_tkcoor_in_board((event.x, event.y))
        tile = self.get_tile(coor)
        if tile is not None:
            tile.on_release(self, tile, coor, event)
            return
        piece = self.get(coor)
        if piece is not None:
            piece.on_release(self, piece, coor, event)
            return

    def reset_tiles(self, init_tile: Tile | None = None) -> None:
        """ボードのタイルをリセットする.

        既存のタイルは全て削除し、 `init_tile` として渡されたタイルを敷き詰める.
        初期タイルが指定されなかった場合、 `None` を敷き詰める.

        Args:
            init_tile (Tile | None, optional): 初期タイル. defaults to None.
        """
        for y in range(self.board_size.y):
            for x in range(self.board_size.x):
                self.__erase_tile((x, y))
        self.__tiles = [[init_tile for _ in range(self.board_size[0])] for _ in range(self.board_size[1])]
        for y in range(self.board_size.y):
            for x in range(self.board_size.x):
                self.__draw_tile(self.get_tile((x, y)), (x, y))

    def __draw_board(self):
        if self.__board_id is not None:
            self.board_canvas.delete(self.__board_id)
        id = self.board_canvas.create_image(
            self.__frame_width, 
            self.__frame_width,
            image=self.__board_image,
            anchor=tkinter.NW,
            tag=BOARD_TAG
        )
        self.__board_id = id

    def __draw_frame(self):
        """フレームの画像を描画する.
        
        既にフレームが描画されている場合、そのフレームを削除して、改めて描画し直す."""
        if self.__frame_id is not None:
            self.board_canvas.delete(self.__frame_id)
        id = self.board_canvas.create_image(
            0, 
            0,
            image=self.__frame_image,
            anchor=tkinter.NW,
            tag=FRAME_TAG
        )
        self.__frame_id = id
    
    def __draw_tile(self, tile: Tile | None, coor: Coordinatelike) -> None:
        if tile is None:
            return
        id = self.board_canvas.create_image(
            self.get_tkcoor_from_board_coor(coor),
            image=tile.image,
            anchor=tkinter.NW,
            tag=TILE_TAG
        )
        tile._id = id
        self.__draw_frame()
    
    def __erase_tile(self, coor: Coordinatelike) -> None:
        tile = self.get_tile(coor)
        if tile is None:
            return
        self.board_canvas.delete(tile._id)
        tile._id = id
    
    def __draw_piece(self, piece: Piece | None) -> None:
        if piece is None:
            return
        if piece._coordinate is None:
            raise InvalidSetCoordinateError(piece)
        id = self.board_canvas.create_image(
            self.get_tkcoor_from_board_coor(piece._coordinate),
            image=piece.image,
            anchor=tkinter.NW,
            tag=PIECE_TAG
        )
        piece._id = id
    
    def __erase_piese(self, piece: Piece | None) -> None:
        if piece is None:
            return
        if piece.coordinate is None:
            raise InvalidSetCoordinateError(piece)
        id = piece._id
        self.board_canvas.delete(id)
        piece._id = id

    def get(self, coordinate: Coordinatelike) -> Piece | None:
        """指定された座標にある駒を取得する
        Args:
            coordinate (Coordinatelike): 座標
        Returns:
            Piece | None: 指定された座標にある駒
        """
        x, y = coordinate
        # self.__board[x][y] は誤りなので注意
        return self.__board[y][x]
    
    def get_all_pieces(self) -> list[Piece]:
        return list(filter(None, [p for row in self.__board for p in row]))

    def take(self, coordinate: Coordinatelike) -> Piece | None:
        """指定された座標にある駒を取得し, その駒をボードから取り除く

        Args:
            coordinate (Coordinatelike): 座標
        Returns:
            Piece | None: 指定された座標にある駒
        """
        piece = self.get(coordinate)
        if piece is not None:
            self.__erase_piese(piece)
            piece._coordinate = None
        x, y = coordinate
        self.__board[y][x] = None
        return piece
    
    def take_all_pieces(self) -> list[Piece]:
        return [self.take(piece.coordinate) for piece in self.get_all_pieces()]

    def put(self, piece: Piece | None, coordinate: Coordinatelike) -> None:
        """指定された座標に駒を配置する. 

        `coordinate` が指定されていない場合は, `piece` の座標を使用する. 

        Args:
            piece (Piece | None): 駒
            coordinate (Coordinatelike | None): 座標.
        """
        self.__erase_piese(self.get(coordinate))    # もともと置いてあった駒を削除

        coordinate = Coordinate(coordinate)
        if piece is not None:
            piece._coordinate = coordinate
            if piece.auto_resize:
                piece.image.resize(self.__space_display_size)
        self.__draw_piece(piece)
        self.__board[coordinate.y][coordinate.x] = piece
    
    def replace(self, piece: Piece | None, coordinate: Coordinatelike) -> Piece | None:
        """指定された座標に駒を配置する.

        Args:
            piece (Piece | None): 新しく置き換える駒
            coordinate (Coordinatelike): 座標.
        Returns:
            Piece | None: 置き換えられた駒
        """
        pre_piece = self.take(coordinate)
        self.put(piece)
        return pre_piece

    def get_tile(self, coordinate: Coordinatelike) -> Tile | None:
        """指定された座標にあるタイルを取得する

        Args:
            coordinate (Coordinatelike): 座標
        Returns:
            Tile | None: 指定された座標にあるタイル
        """
        x, y = coordinate
        return self.__tiles[y][x]

    def replace_tile(self, tile: Tile | None, coordinate: Coordinatelike) -> Tile | None:
        """指定された座標にタイルを配置する

        Args:
            tile (Tile | None): タイル
            coordinate (Coordinatelike): 座標
        """
        pre_tile = self.get_tile(coordinate)
        self.remove_tile(coordinate)
        self.set_tile(tile, coordinate)
        return pre_tile
    
    def set_tile(self, tile: Tile | None, coordinate: Coordinatelike) -> None:
        """指定された座標にタイルを配置する

        Args:
            tile (Tile | None): タイル
            coordinate (Coordinatelike): 座標
        """
        x, y = coordinate
        self.__erase_tile(coordinate)
        if tile is not None:
            tile.image.resize(self.__space_display_size)
        self.__tiles[y][x] = tile
        self.__draw_tile(tile, coordinate)

    def remove_tile(self, coordinate: Coordinatelike):
        """指定された座標にあるタイルを削除する

        Args:
            coordinate (Coordinatelike): 座標
        """
        self.__erase_tile(coordinate)
        x, y = coordinate
        self.__board[y][x] = None