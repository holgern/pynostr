import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from .base_relay import BaseRelay, RelayPolicy
from .event import Event, EventKind
from .key import PublicKey
from .relay_list import RelayList
from .utils import get_public_key

log = logging.getLogger(__name__)


@dataclass
class Contact:
    """Nip-39 Identity.

    :param pub_key: str
    :param relay: str
    :param pet_name: str
    """

    pub_key: str
    relay: Optional[str] = None
    pet_name: Optional[str] = None

    @classmethod
    def from_list(cls, lst: list) -> 'Contact':
        if len(lst) == 3:
            return Contact(pub_key=lst[0], relay=lst[1], pet_name=lst[2])
        elif len(lst) > 0:
            return Contact(pub_key=lst[0])
        else:
            return Contact()

    def to_list(self):
        if self.relay is not None and self.pet_name is not None:
            return [self.pub_key, self.relay, self.pet_name]
        elif self.relay is not None:
            return [self.pub_key, self.relay, ""]
        elif self.pet_name is not None:
            return [self.pub_key, "", self.pet_name]
        else:
            return [self.pub_key]

    def get_pub_key(self):
        return PublicKey.from_hex(self.pub_key)


@dataclass
class ContactList(Event):
    contacts: List[Contact] = field(default_factory=list)
    relays: RelayList = field(default_factory=RelayList)

    def __post_init__(self):
        Event.__post_init__(self)
        self.kind = EventKind.CONTACTS

    @classmethod
    def from_event(cls, event: Event) -> 'ContactList':
        if event.kind != EventKind.CONTACTS:
            return None
        event_dict = event.to_dict()
        cl = ContactList.from_dict(event_dict)
        if event.get_tag_count('p') > 0:
            for tag in event.get_tag_list('p'):
                cl.contacts.append(Contact.from_list(tag))
        if event.content is not None:
            cl.relays = RelayList()
            try:
                cl.relays = RelayList.from_dict(json.loads(event.content))
            except ValueError:
                pass
        return cl

    @classmethod
    def from_dict(cls, msg: dict) -> 'ContactList':
        # "id" is ignore, as it will be computed from the contents
        cl = ContactList(
            content=msg['content'],
            pubkey=msg['pubkey'],
            created_at=msg['created_at'],
            kind=EventKind.SET_METADATA,
            tags=msg['tags'],
            sig=msg['sig'],
        )
        if cl.content is not None and bool(cl.content.strip()):
            try:
                cl.relays = RelayList.from_dict(json.loads(cl.content))
            except ValueError:
                pass
        return cl

    def get_pub_key_list(self):
        pub_keys = []
        for contact in self.contacts:
            pub_keys.append(contact.pub_key)
        return pub_keys

    def add_contact(self, identity_str: str, relay: str = None, pet_name: str = None):
        identity = get_public_key(identity_str)
        self.contacts.append(
            Contact(pub_key=identity.hex(), relay=relay, pet_name=pet_name)
        )

    def add_relay(self, relay: BaseRelay):
        self.relays.append_relay(relay)

    def add(self, url: str, policy: RelayPolicy):
        self.relays.append(url, policy)

    def update(self):
        self.content = json.dumps(self.relays.to_dict())
        self.tags = []
        for contact in self.contacts:
            self.tags.append(["p"] + contact.to_list())
        self.compute_id()

    def __repr__(self):
        return f"ContactList({len(self.contacts)} contacts, {len(self.relays)} relays)"

    def __len__(self):
        return len(self.contacts)

    def __getitem__(self, key):
        return self.contacts[key]

    def __setitem__(self, key, value):
        self.contacts[key] = value

    def __iter__(self):
        return self.contacts.__iter__()

    def __contains__(self, item):
        return item in self.contacts
