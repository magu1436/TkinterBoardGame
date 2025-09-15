from typing import TypeVar, Generic, TypedDict


T = TypeVar("T")
type StateDimension = list[T | None | StateDimension]

class IndexErrorResult(TypedDict):
    ok: bool
    errors: tuple[Exception]


class BoardNdState(Generic[T]):

    def __init__(self, *dimension_sizes: int):
        if len(dimension_sizes) == 0:
            raise ValueError("BoardNdState needs dimension size.")

        self.__state: StateDimension = self.__create_one_dimension(dimension_sizes)
        self.__dimension_sizes: tuple[int] = dimension_sizes
        
    def __create_one_dimension(self, dimension_sizes: tuple[int]) -> StateDimension | None:
        if len(dimension_sizes) > 1:
            target: StateDimension = []
            for d in dimension_sizes:
                target.append(self.__create_one_dimension(dimension_sizes[1:]))
            return target
        
        if len(dimension_sizes) == 1:
            return [None for _ in range(dimension_sizes[0])]
        
        raise ValueError(f"a recieved tuple is incorrect. dimension_sizes: {dimension_sizes}")
    
    def __getitem__(self, indexes: tuple[int] | int) -> None | T:
        """[1, 3]のような値の取得を実装"""
        if type(indexes) == int:
            indexes = tuple(indexes)
        
        check_result = self.__check_index_error(indexes)
        if not check_result["ok"]:
            raise ExceptionGroup("some error happend about index", check_result["errors"])

        target: StateDimension | None | T = self.__state
        for idx in indexes:
            if type(target) != list:
                raise ValueError("some error happened in searching")
            target = target[idx]
        return target
    
    def __setitem__(self, indexes: tuple[int] | int, value: T | None):
        if type(indexes) == int:
            indexes = (indexes,)
        
        check_result = self.__check_index_error(indexes)
        if not check_result["ok"]:
            raise ExceptionGroup("some error happend about index", check_result["errors"])
        
        target: StateDimension | None | T = self.__state
        for idx in indexes[:-1]:
            if type(target) != list:
                raise ValueError("some error happened in searching: 1")
            target = target[idx]
        if type(target) != list:
            raise ValueError("some error happened in searching: 2")
        target[indexes[-1]] = value
        
    
    def __check_index_error(self, indexes: tuple[int]) -> IndexErrorResult:
        """インデックスの指定に不正がないか判定し, その結果を返すメソッド"""
        errors: list[Exception] = []
        if len(indexes) != len(self.__dimension_sizes):
            errors.append(IndexError(f"recieved invalid index: {indexes}"))
        for idx, d in zip(indexes, self.__dimension_sizes):
            if idx < 0 or d < idx: errors.append(IndexError(f" index {idx} is out of range."))
        result: IndexErrorResult = {
            "ok": len(errors) == 0,
            "errors": errors,
        }
        return result
    
    def __str__(self) -> str:
        return str(self.__state)
    
    def __repr__(self) -> str:
        info = {
            "dimension": str(self.__dimension_sizes),
            "state": str(self.__state),
        }
        return str(info)
    
    def __iter__(self):
        # すべての次元を平坦化した一つのリストとしてイテレートする
        if len(self.__dimension_sizes) == 1:
            return iter(self.__state)
        return iter(sum(self.__state, []))


state: BoardNdState[int] = BoardNdState(3)
state[1] = 1
print(state[1:])