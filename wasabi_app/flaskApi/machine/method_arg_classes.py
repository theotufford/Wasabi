from .utils import alph_sort
from collections import UserDict
from typing import NewType
from .containers import Reagent_Mix


class Plate_Map[T](UserDict[T]):
    def __init__(self, source_dict: dict[str, T]):
        print(f"called platemap constructor with type {T.__name__}")
        sorted_ids = alph_sort(list(source_dict.keys()))
        super().__init__({k: source_dict[k] for k in sorted_ids})


def get_plate_value_sum(plate: Plate_Map):
    total = 0
    for val in plate.values():
        total += val
    return total


special_constructors = {
    "Plate_Map": Plate_Map,
}

Named_Container = NewType('Named_Container', str)
Reagent = NewType('Reagent', str)
Volume = NewType('Volume', float)
Wellid = NewType('Wellid', str)
