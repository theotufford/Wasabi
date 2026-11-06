from .utils import alph_sort
from typing import NewType
from .containers import Reagent_Mix



class Plate_Map[T](dict[T]):
    def __init__(self, source_dict: dict[str, T]):
        sorted_ids = alph_sort(list(source_dict.keys()))
        super().__init__({k: source_dict[k] for k in sorted_ids})


class Named_Container(Reagent_Mix):
    def __init__(self, name: str, contents: dict, is_reservoir=False):
        super.__init__(contents, is_reservoir)
        self.name = name


special_constructors = {
    "Plate_Value_Map": Plate_Map,
    "Named_Container": Named_Container
}

Reagent = NewType('Reagent', str)
Volume = NewType('Volume', float)
Wellid = NewType('Volume', str)
