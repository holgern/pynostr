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
from .subscription import Subscription
from .utils import get_relay_information

log = logging.getLogger(__name__)


@dataclass
class RelayPolicy:
    """Relay Read/Write policy.

    :param should_read: bool
    :param should_write: bool
    """

    should_read: bool = True
    should_write: bool = True

    @classmethod
    def from_dict(cls, msg: dict) -> 'RelayPolicy':
        return RelayPolicy(should_read=msg["read"], should_write=msg["write"])

    def to_dict(self) -> Dict[str, bool]:
        return {"read": self.should_read, "write": self.should_write}

    def __str__(self):
        return str(self.to_dict())


@dataclass
class RelayProxyConnectionConfig:
    host: str
    port: int
    type: str


class BaseRelay:
    def __init__(
        self,
        url: str,
        policy: RelayPolicy,
        message_pool: MessagePool = MessagePool(),
        timeout: float = 2.0,
        close_on_eose: bool = True,
        message_callback=None,
        message_callback_url=False,
    ) -> None:
        self.url = url
        self.policy = policy
        self.message_pool = message_pool
        self.timeout = timeout
        self.close_on_eose = close_on_eose
        self.lock: Lock = Lock()
        self.metadata = None
        self.subscriptions: dict[str, Subscription] = {}
        self.connected: bool = False
        self.eose_counter: int = 0
        self.eose_threshold: int = 0
        self.error_counter: int = 0
        self.error_threshold: int = 3
        self.timeout_error_counter: int = 0
        self.timeout_error_threshold: int = 10
        self.num_sent_events: int = 0
        self.message_callback = message_callback
        self.message_callback_url = message_callback_url
        self.outgoing_messages = Queue()

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "policy": self.policy.to_dict(),
            "subscriptions": [
                subscription.to_dict() for subscription in self.subscriptions.values()
            ],
        }

    def update_metadata(self, timeout: float = None) -> None:
        if timeout is None:
            timeout = self.timeout
        self.metadata = get_relay_information(self.url, timeout=timeout, add_url=False)

    def check_nip(self, nip: int) -> bool:
        if self.metadata is None:
            self.update_metadata()
        if self.metadata is None:
            return False
        if "supported_nips" not in self.metadata:
            return False
        return nip in self.metadata["supported_nips"]

    def add_subscription(self, id, filters: FiltersList):
        with self.lock:
            self.subscriptions[id] = Subscription(id, filters)
            self.publish(self.subscriptions[id].to_message())
            self.eose_threshold += 1

    def close_subscription(self, id: str) -> None:
        with self.lock:
            self.subscriptions.pop(id, None)

    def update_subscription(self, id: str, filters: FiltersList) -> None:
        with self.lock:
            subscription = self.subscriptions[id]
            subscription.filters = filters
            self.eose_threshold += 1
            self.publish(self.subscriptions[id].to_message())

    def _on_message(self, message):
        if self._is_valid_message(message):
            message_json = json.loads(message)
            if self.message_callback is not None:
                if self.message_callback_url:
                    self.message_callback(message_json, self.url)
                else:
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
        self.eose_counter += 1
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
