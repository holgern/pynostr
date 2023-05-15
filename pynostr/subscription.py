import json
from dataclasses import dataclass

from .filters import FiltersList
from .message_type import ClientMessageType


@dataclass
class Subscription:
    id: str
    filtersList: FiltersList

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError("Argument 'id' must be of type str")

    def to_dict(self):
        return {"id": self.id, "filters": self.filtersList.to_json_array()}

    def to_message(self) -> str:
        message = [ClientMessageType.REQUEST, self.id]
        message.extend(self.filtersList.to_json_array())
        return json.dumps(message)

    def to_nip45_count_message(self) -> str:
        """
            NIP-45: https://github.com/nostr-protocol/nips/blob/master/45.md

            returns int
            returns count of Events passing the set of Filters
                    attached to a Subscription
        """
        message = [ClientMessageType.COUNT, self.id]
        message.extend(self.filtersList.to_json_array())
        return json.dumps(message)
