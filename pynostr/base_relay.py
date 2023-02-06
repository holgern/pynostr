from dataclasses import dataclass
from threading import Lock
from typing import Dict

from .message_pool import MessagePool
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
