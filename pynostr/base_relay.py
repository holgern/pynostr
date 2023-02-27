import json
import logging
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import Dict

from .event import Event
from .filters import FiltersList
from .message_pool import MessagePool
from .message_type import RelayMessageType
from .request import Request
from .subscription import Subscription

log = logging.getLogger(__name__)


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
        timeout: float = 2.0,
        close_on_eose: bool = True,
        message_callback=None,
    ) -> None:
        self.url = url
        self.message_pool = message_pool
        self.policy = policy
        self.ssl_options = ssl_options
        self.proxy_config = proxy_config
        self.timeout = timeout
        self.close_on_eose = close_on_eose
        self.lock: Lock = Lock()
        self.ws = None
        self.subscriptions: dict[str, Subscription] = {}
        self.connected: bool = False
        self.error_counter: int = 0
        self.error_threshold: int = 10
        self.num_sent_events: int = 0
        self.request: str = ""
        self.message_callback = message_callback
        self.outgoing_messages = Queue()

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

    def _on_message(self, message):
        if self._is_valid_message(message):
            message_json = json.loads(message)
            if self.message_callback is not None:
                self.message_callback(message_json)
            message_type = message_json[0]
            if message_type == RelayMessageType.EVENT:
                # event = Event.from_dict(message_json[2])
                # print(event.to_message())
                self.message_pool.add_message(message, self.url)
            elif message_type == RelayMessageType.END_OF_STORED_EVENTS:
                self._eose_received()
                self.message_pool.add_message(message, self.url)
            elif message_type == RelayMessageType.OK:
                self.message_pool.add_message(message, self.url)
            elif message_type == RelayMessageType.AUTH:
                print(message)

    def publish(self, message: str):
        self.outgoing_messages.put(message)

    def _eose_received(self):
        return

    def _is_valid_message(self, message: str) -> bool:
        if message is None:
            return False
        message = message.strip("\n")
        if not message or message[0] != "[" or message[-1] != "]":
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
        elif message_type == RelayMessageType.OK:
            if not len(message_json) == 4:
                return False
            if message_json[2] in ["true", "false"]:
                return True
            elif isinstance(message_json[2], bool):
                return True
            else:
                return False
        return True
