from __future__ import annotations

from functools import singledispatchmethod
from PIL import Image, ImageTk
import tkinter
from tkinter import PhotoImage
from typing import Sequence, Literal, overload
import math


SEARCHING_TRANSPARENT_PIXEL_COUNT = 50
MOVING_DISTANCE_RATIO_TO_SEARCH = 0.005
TRELENT_TRANSPARAET_PIXEL_VALUE = 10
SEARCHING_FRAME_SEPARATER = 3


type PathOrImage = str | Image.Image | ImageTk.PhotoImage | PhotoImage


def transparent_image(size: tuple[int, int] | list[int] | None = None) -> Image.Image:
    """透明な画像を生成する

    Args:
        size(Sequence[int], optional): 生成する画像の大きさ. default to None.

    Returns:
        Image.Image: 透明な画像
    """
    if size is None:
        size = (int(1), int(1))
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    return image


class BoardGamePhotoImage(ImageTk.PhotoImage):
    """PIL.ImageTk.PhotoImageを拡張したクラス"""

    def __init__(
            self, 
            image: PathOrImage | None = None, 
            size: Sequence[int] | None = None, 
            fit_to: Literal["width", "height"] | None = None
            ) -> None:
        """コンストラクタ

        `image` を何も指定しないとき, 透明な画像を作成する.
        
        Args:
            image(PathOrImage | None, optional): 画像オブジェクトまたはパス. Default to None.
            size(Sequence[int]) | None, optional): 画像のサイズ. Default to None.
            fit_to(Literal['width','height']): 縦横比をどちらにあわせるか. Noneのときはリサイズしない
        """
        match image:
            case str(): image = self.__str2image(image)
            case ImageTk.PhotoImage(): image = ImageTk.getimage(image)
            case PhotoImage(): image = ImageTk.getimage(image)
            case None: image = transparent_image()

        if image.mode != "RGBA":
            image = image.convert("RGBA")
        if size is not None:
            if fit_to == "width":
                image = image.resize((size[0], int(image.height * size[0] / image.width)))
            elif fit_to == "height":
                image = image.resize((int(image.width * size[1] / image.height), size[1]))
            else:
                image = image.resize(size)
        super().__init__(image=image)
        self.__pil_image = image
    
    def __str2image(self, path: str) -> None:
        """コンストラクタ

        Args:
            path (str): 画像のパス
        
        Returns:
            FileNotFountError: 画像パスが見つからなかったときに生じる
        """
        try:
            image = Image.open(path).convert("RGBA")
            return image
        except FileNotFoundError as e:
            raise e
    
    def copy(self) -> BoardGamePhotoImage:
        """画像をコピーする

        Returns:
            BoardGamePhotoImage: コピーした画像
        """
        image = self.__pil_image.copy()
        return BoardGamePhotoImage(image)
    
    def resize(self, size: Sequence[int]):
        """画像を指定のサイズになるよう拡大・縮小する.
        
        `size` の値に `0` 以下が含まれるとき、その値を `1` に変換してリサイズする.
        
        Args:
            size(Sequence[int]): リサイズ後の大きさ
        """
        valid_size = []
        for coor_v in size:
            if coor_v < 1:
                valid_size.append(1)
            else:
                valid_size.append(coor_v)
        img = self.__pil_image.resize(valid_size)
        self.__pil_image = img
        super().__init__(img)

    def put_on(self, image: BoardGamePhotoImage, position: Sequence[int]):
        """自身に画像を貼り付けるためのメソッド

        Args:
            image (BoardGamePhotoImage): 貼り付ける画像
            position (Sequence[int]): 貼り付ける位置
        """
        put_img = image.__pil_image
        origin_image = self.__pil_image
        origin_image.paste(put_img, tuple(position), put_img)
        self.__pil_image = origin_image
        super().__init__(origin_image)
    
    def rotate(self, angle: int | float):
        """自身を回転させるためのメソッド.
        
        回転角は度数法で与える.
        
        Args:
            angle(int | float): 回転角"""
        img = self.__pil_image
        rotated_img = img.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        self.__pil_image = rotated_img
        super().__init__(rotated_img)
    
    def to_pillow_image(self) -> Image:
        return self.__pil_image.copy()


def get_frame_width(frame_image: BoardGamePhotoImage) -> int:
    """フレームの幅を取得する

    フレームの画像は、必ずリサイズ済のものを使用すること.
    フレームの左右の辺の中心の位置と、その位置から縦の長さの1/4だけ上下にずらした地点の三箇所、  
    上下の辺の同様の三箇所の幅を計算し、そのうち最小のものをフレームの幅として返す.

    Args:
        frame_image (BoardGamePhotoImage): フレーム画像

    Returns:
        int: フレームの幅
    """
    frame_image = frame_image._BoardGamePhotoImage__pil_image

    # 上下左右の順番で探索
    directions = (
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0)
    )
    move_corsor = lambda corsor, direction, distance: (
        corsor[0] + direction[0] * distance,
        corsor[1] + direction[1] * distance
    )

    width, height = frame_image.width, frame_image.height
    sep_width, sep_height = width // (SEARCHING_FRAME_SEPARATER + 1), height // (SEARCHING_FRAME_SEPARATER + 1)
    move_distance = int(width * MOVING_DISTANCE_RATIO_TO_SEARCH)    # 一回の探索で移動する距離
    check_points = []   # 探索の終点の座標を格納するリスト
    for i in range(1, SEARCHING_FRAME_SEPARATER + 1):
        check_points.append((i * sep_width, 0))
        check_points.append((i * sep_width, height))
        check_points.append((0, i * sep_height))
        check_points.append((width, i * sep_height))
    init_cursors = []   # 探索の始点を格納するリスト。この始点から４方向に探索する
    for i in range(SEARCHING_FRAME_SEPARATER):
        init_cursors.append((check_points[i * 4][0], check_points[i * 4 + 2][1]))

    widths = []

    for cursor in init_cursors:
        for direction in directions:
            searching_cursor = cursor
            for i in range(SEARCHING_TRANSPARENT_PIXEL_COUNT):
                searching_cursor = move_corsor(searching_cursor, direction, move_distance)
                if frame_image.getpixel(searching_cursor)[3] >= TRELENT_TRANSPARAET_PIXEL_VALUE:
                    widths.append(
                        int(min([math.sqrt((ing[0] - searching_cursor[0])**2 + (ing[1] - searching_cursor[1])**2) for ing in check_points]))
                    )
                    break
    return min(widths)
        


if __name__ == "__main__":
    root = tkinter.Tk()
    root.geometry("800x800")
    root.title("test")
    img = Image.open("images/grid.png").resize((400, 800))
    img_ = BoardGamePhotoImage(img)
    canvas = tkinter.Canvas(root, width=400, height=800)
    canvas.create_image(0, 0, image=img_, anchor=tkinter.NW)
    img_2 = img_.copy()
    img_2.rotate(90)
    canvas2 = tkinter.Canvas(root, width=400, height=800)
    canvas2.create_image(0, 0, image=img_2, anchor=tkinter.NW)
    canvas.place(x=0, y=0)
    canvas2.place(x=400, y=400)
    img_2._BoardGamePhotoImage__pil_image.save("images/test.png", format="PNG")
    print(img_2.width(), img_2.height())
    root.mainloop()