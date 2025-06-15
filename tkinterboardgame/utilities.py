from __future__ import annotations

from typing import Any, overload, Sequence, Union
from copy import deepcopy


class BoardGameUtilitiesException(Exception):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class UnsupportedOperandError(BoardGameUtilitiesException):
    """サポートされていないオペランド同士の演算が行われたときの生じる

    Args:
        operand(str): オペランド
        value1(Any): 演算を行おうとしたオブジェクト1
        value2(Any): 演算を行おうとしたオブジェクト2
    """
    def __str__(self):
        operand = self.args[0]
        v1_class_name = self.args[1].__class__.__name__
        v2_class_name = self.args[2].__class__.__name__
        return f"unsupported operand types for {operand}: '{v1_class_name}' and '{v2_class_name}'"

class UncoordinatelikeValueArgError(BoardGameUtilitiesException):
    """座標系でないオブジェクトを引数に受け取った場合に生じる.
    
    Args:
        uncoordinatelike_obj(Any): 座標を表さないオブジェクト"""
    
    def __str__(self):
        uncoordinatelike_obj = self.args[0]
        return f"Recieve uncoordinatelike object: {uncoordinatelike_obj}"



XYKEY = ["x", "y"]


type CoordinateValue = int | float
type Coordinatelike = Coordinate | tuple | list | Sequence


class Coordinate(list):
    """座標を表すクラス

    2次元の座標を保持する.
    座標はリストとして表現され、0番目の要素がx座標、1番目の要素がy座標となる.
    リストとしての操作が可能で、加算や減算などの演算もサポートされている.
    
    Attributes:
        x (CoordinateValue): x座標
        y (CoordinateValue): y座標
    """

    @overload
    def __init__(self, coordinate: Sequence[CoordinateValue]) -> None:
        """
        コンストラクタ

        Args:
            coordinate (Sequence[CoordinateValue]): 座標
        """
    @overload
    def __init__(self, x: CoordinateValue, y: CoordinateValue) -> None:
        """
        コンストラクタ

        Args:
            x (CoordinateValue): x座標
            y (CoordinateValue): y座標
        """

    def __init__(self, x_or_coor: Sequence[CoordinateValue] | CoordinateValue, y: CoordinateValue | None = None):
        if isinstance(x_or_coor, CoordinateValue.__value__):
            coor: list = [x_or_coor, y]
        else:
            coor: Sequence[CoordinateValue] = x_or_coor
        super().__init__(coor)
    
    @property
    def x(self) -> CoordinateValue:
        return self[0]
    
    @x.setter
    def x(self, value):
        self[0] = value
    
    @property
    def y(self) -> CoordinateValue:
        return self[1]
    
    @y.setter
    def y(self, value):
        self[1] = value
    
    def __getitem__(self, index: Any) -> CoordinateValue:
        if index in XYKEY:
            return getattr(self, index)
        return super().__getitem__(index)
    
    def __setitem__(self, index, value):
        if index in XYKEY:
            for i in len(XYKEY):
                if index == XYKEY[i]:
                    index = i
                    break
        return super().__setitem__(index, value)
    
    def __add__(self, other: Coordinatelike) -> Coordinate:
        if not isinstance(other, Coordinatelike.__value__):
            raise UnsupportedOperandError("+", self, other)
        return Coordinate([s + o for s, o in zip(self, other)])
    
    def __iadd__(self, other: Coordinatelike) -> Coordinate:
        return self.__add__(other)
    
    def __radd__(self, other: Coordinatelike) -> Coordinate:
        return self.__add__(other)
    
    def __sub__(self, other: Coordinatelike) -> Coordinate:
        if not isinstance(other, Coordinatelike.__value__):
            raise UnsupportedOperandError("-", self, other)
        other = [-1 * value for value in other]
        return self.__add__(other)
    
    def __rsub__(self, other: Coordinatelike) -> Coordinate:
        return Coordinate(other).__sub__(self)
    
    def __mul__(self, other: CoordinateValue | Coordinatelike) -> Coordinate:
        if isinstance(other, CoordinateValue.__value__):
            self = deepcopy(self)
            return Coordinate(tuple(map(lambda x: x * other, self)))
        if isinstance(other, Coordinatelike.__value__):
            try:
                return Coordinate([v1 * v2 for v1, v2 in zip(self, other, strict=True)])
            except ValueError:
                raise UncoordinatelikeValueArgError(other)
        raise UnsupportedOperandError("*", self, other)
    
    def __rmul__(self, other: CoordinateValue | Coordinatelike) -> Coordinate:
        try:
            return self.__mul__(other)
        except UncoordinatelikeValueArgError as e:
            raise e
        except UnsupportedOperandError as e:
            raise e
    
    def __truediv__(self, other: CoordinateValue) -> Coordinate:
        if not isinstance(other, CoordinateValue.__value__):
            raise UnsupportedOperandError("/", self, other)
        self = deepcopy(self)
        return Coordinate(tuple(map(lambda x: x / other, self)))
    
    def __floordiv__(self, other: CoordinateValue) -> Coordinate:
        if not isinstance(other, CoordinateValue.__value__):
            raise UnsupportedOperandError("//", self, other)
        self = deepcopy(self)
        return Coordinate(tuple(map(lambda x: x // other, self)))
    
    def __iter__(self):
        yield self[0]
        yield self[1]