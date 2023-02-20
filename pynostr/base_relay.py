import json
import logging
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import Dict

import requests

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
        close_on_eose: bool = True,
    ) -> None:
        self.url = url
        self.message_pool = message_pool
        self.policy = policy
        self.ssl_options = ssl_options
        self.proxy_config = proxy_config
        self.close_on_eose = close_on_eose
        self.lock: Lock = Lock()
        self.ws = None
        self.subscriptions: dict[str, Subscription] = {}
        self.connected: bool = False
        self.error_counter: int = 0
        self.error_threshold: int = 10
        self.num_sent_events: int = 0
        self.request: str = ""
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
            if message_type[2] not in ["true", "false"]:
                return False
        return True

    def get_relay_information(self):
        headers = {'Accept': 'application/nostr+json'}
        if "wss" in self.url:
            metadata_uri = self.url.replace("wss", "https")
        elif "ws" in self.url:
            metadata_uri = self.url.replace("ws", "http")
        else:
            raise Exception(f"{self.url} is not a websocket url")
        try:
            response = requests.get(metadata_uri, headers=headers, timeout=5)

            response.raise_for_status()

            metadata = response.json()
            return metadata
        except requests.exceptions.Timeout:
            # Handle a timeout error
            log.warning("Request timed out. Please try again later.")

        except requests.exceptions.HTTPError as err:
            # Handle an HTTP error
            log.warning(f"HTTP error occurred: {err}")

        except requests.exceptions.RequestException as err:
            # Handle any other request exception
            log.warning(f"An error occurred: {err}")
