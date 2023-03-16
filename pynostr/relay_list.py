import concurrent.futures
import logging
from dataclasses import dataclass, field
from itertools import repeat
from typing import List

from .base_relay import BaseRelay, RelayPolicy
from .utils import get_relay_information

log = logging.getLogger(__name__)


@dataclass
class RelayList:
    data: List[BaseRelay] = field(default_factory=list)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return self.data.__iter__()

    def __contains__(self, item):
        return item in self.data

    @classmethod
    def from_dict(cls, msg: dict) -> 'RelayList':
        rl = RelayList()
        for url in msg:
            if (
                isinstance(msg[url], dict)
                and "read" in msg[url]
                and "write" in msg[url]
            ):
                rl.append(url, RelayPolicy.from_dict(msg[url]))
        return rl

    def to_dict(self) -> dict:
        ret = {}
        for relay in self.data:
            ret[relay.url] = relay.policy.to_dict()
        return ret

    def append_relay(self, relay: BaseRelay):
        if self.check_url(relay.url) and relay.url not in self.get_url_list():
            self.data.append(relay)

    def append(self, url: str, policy: RelayPolicy = RelayPolicy()):
        if policy and self.check_url(url) and url not in self.get_url_list():
            self.data.append(BaseRelay(url, policy))

    def append_url_list(self, url_list: List[str], policy: RelayPolicy = RelayPolicy()):
        for url in url_list:
            self.append(url, policy)

    def get_url_list(self):
        url_list = []
        for d in self.data:
            url_list.append(d.url)
        return url_list

    def check_url(self, url: str):
        if not url or not bool(url.strip()):
            return False
        if "ws" not in url:
            return False
        if "." not in url:
            return False
        return True

    def update_relay_information(self, max_workers=16, timeout=2):
        relay_list = []
        relays = {}
        for relay in self.data:
            relay_list.append(relay.url)
            relay.metadata = None
            relays[relay.url] = relay
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            res = executor.map(get_relay_information, relay_list, repeat(timeout))
            for relay_info in res:
                if relay_info is not None:
                    relays[relay_info.pop("url")].metadata = relay_info
        self.data = list(relays.values())

    def drop_empty_metadata(self):
        old_data = self.data.copy()
        self.data = []
        for relay in old_data:
            if relay.metadata is not None:
                self.data.append(relay)


# @dataclass
# class RelayListMetadata:
