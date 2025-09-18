from typing import TypeVar, Generic, TypedDict


_T = TypeVar("_T")
type _StateDimension = list[_T | None | _StateDimension]

class _IndexErrorResult(TypedDict):
    ok: bool
    errors: tuple[Exception]


class BoardStateND(Generic[_T]):
    """N次元の盤面状況を保持するための多次元配列クラス."""

    def __init__(self, *dimension_sizes: int, init_value: _T | None = None):
        """コンストラクタ
        
        Args:
            *dimension_size(int): 各次元の要素数. 最低でも1次元は定義しなければエラーとなる.
            init_value(_T, None): 初期値. Default to None.
        """
        if len(dimension_sizes) == 0:
            raise ValueError("BoardNdState needs dimension size.")
        
        self.__init_value: _T | None = init_value

        self._state: _StateDimension = self.__create_one_dimension(dimension_sizes)
        self.__dimension_size: tuple[int] = dimension_sizes
        
    def __create_one_dimension(self, dimension_sizes: tuple[int]) -> _StateDimension | None:
        """各次元のリストを再帰的に作成するメソッド."""
        if len(dimension_sizes) > 1:
            target: _StateDimension = []
            for _ in range(dimension_sizes[0]):
                target.append(self.__create_one_dimension(dimension_sizes[1:]))
            return target
        
        if len(dimension_sizes) == 1:
            return [self.__init_value for _ in range(dimension_sizes[0])]
        
        raise ValueError(f"a received tuple is incorrect. dimension_sizes: {dimension_sizes}")
    
    def __getitem__(self, indexes: tuple[int] | int | tuple[slice] | slice) -> None | _T:
        """[1, 3], [1:, 3:5]のような値の取得を実装  
        
        TODO: [1, 1:] のようなintとsliceの複合のインデックス指定に対応
        """
        # 引数が全て同じ型であるか判定. 複合に対応していない限りは必要.
        if (isinstance(indexes, tuple)) and not(len({type(v) for v in indexes}) <= 1):
            raise IndexError(f"all args must be same type. args: {indexes}")
        
        match indexes:
            case tuple():
                match indexes[0]:
                    case int(): return self.__get_value_with_tuple_or_int(indexes)
                    case slice(): return self.__get_values_with_slice(indexes, self._state)
            case int():
                return self.__get_value_with_tuple_or_int(indexes)
            case slice():
                return self.__get_values_with_slice(indexes, self._state)
    
    def __get_value_with_tuple_or_int(self, indexes: tuple[int] | int) -> None | _T:
        """intのインデックス指定で値を取得するメソッド"""
        
        if type(indexes) == int:
            indexes = tuple(indexes)
        
        check_result = self.__check_index_error(indexes)
        if not check_result["ok"]:
            raise ExceptionGroup("some error happened about index", check_result["errors"])

        target: _StateDimension | None | _T = self._state
        for idx in indexes:
            if type(target) != list:
                raise ValueError("some error happened in searching")
            target = target[idx]
        return target
    
    def __get_values_with_slice(self, index_slices: tuple[slice], target_list: list[_StateDimension | _T | None]):
        """sliceのインデックス指定で値を取得するメソッド"""
        if len(index_slices) == 1: return target_list[index_slices[0]]

        result = []
        original_lists = target_list[index_slices[0]]
        for l in original_lists:
            result.append(self.__get_values_with_slice(index_slices[1:], l))
        return result
    
    def __setitem__(self, indexes: tuple[int] | int, value: _T | None):
        if type(indexes) == int:
            indexes = (indexes,)
        
        check_result = self.__check_index_error(indexes)
        if not check_result["ok"]:
            raise ExceptionGroup("some error happened about index", check_result["errors"])
        
        target: _StateDimension | None | _T = self._state
        for idx in indexes[:-1]:
            if type(target) != list:
                raise ValueError("some error happened in searching: 1")
            target = target[idx]
        if type(target) != list:
            raise ValueError("some error happened in searching: 2")
        target[indexes[-1]] = value
    
    def __check_index_error(self, indexes: tuple[int] | tuple[slice]) -> _IndexErrorResult:
        """インデックスの指定に不正がないか判定し, その結果を返すメソッド"""
        errors: list[Exception] = []
        if len(indexes) != len(self.__dimension_size):
            errors.append(IndexError(f"received invalid index: {indexes}"))

        if isinstance(indexes[0], int):
            for idx, d in zip(indexes, self.__dimension_size):
                if idx < 0 or d < idx: errors.append(IndexError(f" index {idx} is out of range."))

        result: _IndexErrorResult = {
            "ok": len(errors) == 0,
            "errors": errors,
        }
        return result
    
    def __str__(self) -> str:
        return str(self._state)
    
    def __repr__(self) -> str:
        info = {
            "dimension": str(self.__dimension_size),
            "state": str(self._state),
        }
        return str(info)
    
    def __iter__(self):
        # すべての次元を平坦化した一つのリストとしてイテレートする
        if len(self.__dimension_size) == 1:
            return iter(self._state)
        return iter(sum(self._state, []))
    
    @property
    def dimension_size(self):
        return self.__dimension_size


class BoardState2D(BoardStateND):
    def __init__(self, x: int, y: int, init_value: _T | None = None):
        super().__init__(x, y, init_value=init_value)
    
    @property
    def rows(self) -> tuple[tuple[_T, None]]:
        return tuple(map(lambda row: tuple(row), self._state))
    
    @property
    def columns(self) -> tuple[tuple[_T, None]]:
        sorted_list = [[] for _ in range(self.dimension_size[1])]
        for row in self._state[0]:
            for col in self._state[1]:
                sorted_list[col][row]
        return tuple(map(lambda col: tuple(col), self._state))