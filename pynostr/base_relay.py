import json
from dataclasses import dataclass
from threading import Lock
from typing import Dict

from .event import Event
from .filters import FiltersList
from .message_pool import MessagePool
from .message_type import RelayMessageType
from .request import Request
from .subscription import Subscription


@dataclass
class RelayPolicy:
    should_read: bool = True
    should_write: bool = True

    def to_json_object(self) -> Dict[str, bool]:
        return {"read": self.should_read, "write": self.should_write}


@dataclass
class RelayProxyConnectionConfig:
    host: str
    port: int
    type: str


class BaseRelay:
    def __init__(
        self,
        url: str,
        message_pool: MessagePool,
        policy: RelayPolicy = RelayPolicy(),
        ssl_options: dict = None,
        proxy_config: RelayProxyConnectionConfig = None,
    ) -> None:
        self.url = url
        self.message_pool = message_pool
        self.policy = policy
        self.ssl_options = ssl_options
        self.proxy_config = proxy_config
        self.lock: Lock = Lock()
        self.ws = None
        self.subscriptions: dict[str, Subscription] = {}
        self.connected: bool = False
        self.reconnect: bool = True
        self.error_counter: int = 0
        self.error_threshold: int = 10
        self.request: str = ""

    def __repr__(self):
        return json.dumps(self.to_json_object(), indent=2)

    def to_json_object(self) -> dict:
        return {
            "url": self.url,
            "policy": self.policy.to_json_object(),
            "subscriptions": [
                subscription.to_json_object()
                for subscription in self.subscriptions.values()
            ],
            "request": self.request,
        }

    def add_subscription(self, id, filters: FiltersList):
        with self.lock:
            self.subscriptions[id] = Subscription(id, filters)
            self.request = Request(id, filters).to_message()

    def close_subscription(self, id: str) -> None:
        with self.lock:
            self.subscriptions.pop(id, None)

    def update_subscription(self, id: str, filters: FiltersList) -> None:
        with self.lock:
            subscription = self.subscriptions[id]
            subscription.filters = filters
            self.request = Request(id, filters).to_message()

    def _is_valid_message(self, message: str) -> bool:
        message = message.strip("\n")
        if not message or message[0] != '[' or message[-1] != ']':
            return False

        message_json = json.loads(message)
        message_type = message_json[0]
        if not RelayMessageType.is_valid(message_type):
            return False
        if message_type == RelayMessageType.EVENT:
            if not len(message_json) == 3:
                return False

            subscription_id = message_json[1]
            with self.lock:
                if subscription_id not in self.subscriptions:
                    return False

            event = Event.from_dict(message_json[2])
            if not event.verify():
                return False

            with self.lock:
                subscription = self.subscriptions[subscription_id]

            if subscription.filtersList and not subscription.filtersList.match(event):
                return False

        return True
