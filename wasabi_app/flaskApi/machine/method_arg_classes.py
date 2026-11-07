from .utils import alph_sort
from collections import UserDict
from typing import NewType
from .containers import Reagent_Mix


class Plate_Map[T](UserDict[T]):
    def __init__(self, source_dict: dict[str, T]):
        print(f"called platemap constructor with type {T.__name__}")
        sorted_ids = alph_sort(list(source_dict.keys()))
        super().__init__({k: source_dict[k] for k in sorted_ids})


class Volume_Map(Plate_Map[float]):
    def __init__(self, source_dict: dict[str, float]):
        super().__init__(source_dict)

    def get_value_sum(self):
        total = 0
        for val in self.values():
            total += val
        return total


special_constructors = {
    "Plate_Map": Plate_Map,
    "Volume_Map": Volume_Map,
}

Named_Container = NewType('Named_Container', str)
Reagent = NewType('Reagent', str)
Volume = NewType('Volume', float)
Wellid = NewType('Volume', str)
