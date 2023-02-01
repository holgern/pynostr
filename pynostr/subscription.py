from dataclasses import dataclass

from .filters import FiltersList


@dataclass
class Subscription:
    id: str
    filtersList: FiltersList

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError("Argument 'id' must be of type str")

    def to_json_object(self):
        return {"id": self.id, "filters": self.filtersList.to_json_array()}
