import json
from dataclasses import dataclass

from .filters import FiltersList
from .message_type import ClientMessageType


@dataclass
class Request:
    subscription_id: str
    filtersList: FiltersList

    def to_message(self) -> str:
        message = [ClientMessageType.REQUEST, self.subscription_id]
        message.extend(self.filtersList.to_json_array())
        return json.dumps(message)
