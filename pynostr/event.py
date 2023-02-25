"""Inspired by event.py from https://github.com/jeffthibault/python-nostr.git."""
import binascii
import datetime
import json
import time
from dataclasses import dataclass
from enum import IntEnum
from hashlib import sha256
from typing import List, Optional

from .key import PrivateKey, PublicKey
from .message_type import ClientMessageType
from .utils import bech32_encode


class EventKind(IntEnum):
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_RELAY = 2
    CONTACTS = 3
    ENCRYPTED_DIRECT_MESSAGE = 4
    DELETE = 5
    REACTION = 7
    BADGE_AWARD = 8
    CHANNEL_CREATE = 40
    CHANNEL_META = 41
    CHANNEL_MESSAGE = 42
    CHANNEL_HIDE = 43
    CHANNEL_MUTE = 44
    REPORT = 1984
    ZAP_REQUEST = 9734
    ZAPPER = 9735
    RELAY_LIST_METADATA = 10002
    PROFILE_BADGES = 30008
    BADGE_DEFINITION = 30009
    LONG_FORM_CONTENT = 30023


@dataclass
class Event:
    """Event class.

    :param content: content string
    :param pukey: public key in hex form
    :param created_at: event creation date
    :param kind: event kind
    :param tags: list of list of strings
    :param id: event id, will be computed
    :param sig: signature, will be created after signing with a private key
    """

    content: Optional[str] = None
    pubkey: Optional[str] = None
    created_at: Optional[int] = None
    kind: Optional[int] = EventKind.TEXT_NOTE
    tags: List[List[str]] = None
    id: Optional[str] = None
    sig: Optional[str] = None

    def __post_init__(self):
        if self.content is not None and not isinstance(self.content, str):
            # DMs initialize content to None but all other kinds should pass in a str
            raise TypeError("Argument 'content' must be of type str")
        if self.created_at is None:
            self.created_at = int(time.time())

        if self.tags is None:
            self.tags = []

        if self.id is None:
            self.compute_id()

    def serialize(self) -> bytes:
        data = [0, self.pubkey, self.created_at, self.kind, self.tags, self.content]
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        return data_str.encode()

    def compute_id(self):
        self.id = sha256(self.serialize()).hexdigest()

    @classmethod
    def from_dict(cls, msg: dict) -> 'Event':
        # "id" is ignore, as it will be computed from the contents
        return Event(
            content=msg['content'],
            pubkey=msg['pubkey'],
            created_at=msg['created_at'],
            kind=msg['kind'],
            tags=msg['tags'],
            sig=msg['sig'],
        )

    def add_pubkey_ref(self, pubkey: str):
        """Adds a reference to a pubkey as a 'p' tag."""
        self.tags.append(['p', pubkey])
        self.compute_id()

    def has_pubkey_ref(self, pubkey: str):
        for tag in self.tags:
            if not tag and len(tag) < 2:
                continue
            if tag[0] == 'p' and tag[1] == pubkey:
                return True
        return False

    def add_event_ref(self, event_id: str):
        """Adds a reference to an event_id as an 'e' tag."""
        self.tags.append(['e', event_id])
        self.compute_id()

    def has_event_ref(self, event_id: str):
        """Check if a e tag to the given event_id exists."""
        for tag in self.tags:
            if not tag and len(tag) < 2:
                continue
            if tag[0] == 'e' and tag[1] == event_id:
                return True
        return False

    def get_tag_dict(self):
        """Returns all tags as dict."""
        ret = {}
        tag_types = self.get_tag_types()
        for t in tag_types:
            ret[t] = self.get_tag_list(tag_type=t)
        return ret

    def get_tag_list(self, tag_type: str = 'e'):
        """Returns all tags of given type as list."""
        ret = []
        for tag in self.tags:
            if not tag and len(tag) < 2:
                continue
            if tag[0] == tag_type:
                ret.append(tag[1])
        return ret

    def get_tag_types(self):
        """Returns list of all included tag types."""
        ret = []
        for tag in self.tags:
            if not tag and len(tag) == 0:
                continue
            if tag[0] not in ret:
                ret.append(tag[0])
        return ret

    def get_tag_count(self, tag_type: str = 'e'):
        """Returns all tags of given type as list."""
        count = 0
        for tag in self.tags:
            if len(tag) > 0 and tag[0] == tag_type:
                count += 1
        return count

    def bech32(self) -> str:
        """bech32-encoded entities (N-19)

        :return: note id as bech32 encoding with note prefix
        """
        self.compute_id()
        return bech32_encode(binascii.unhexlify(self.id), "note")

    def sign(self, private_key_hex: str) -> None:
        """signs the event with the private key and stored the signature in self.sig.
        The pubkey from the event is replaced and the note id recomputed.

        :param private_key_hex: private key as hex string
        """
        if self.kind == EventKind.ENCRYPTED_DIRECT_MESSAGE and self.content is None:
            raise Exception("Message is not yet encrypted!")
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        self.pubkey = sk.public_key.hex()
        self.compute_id()
        sig = sk.sign(bytes.fromhex(self.id))
        self.sig = sig.hex()

    def verify(self) -> bool:
        pub_key = PublicKey.from_hex(self.pubkey)
        self.compute_id()
        return pub_key.verify(bytes.fromhex(self.sig), bytes.fromhex(self.id))

    def date_time(self):
        return datetime.datetime.utcfromtimestamp(self.created_at)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pubkey": self.pubkey,
            "created_at": self.created_at,
            "kind": self.kind,
            "tags": self.tags,
            "content": self.content,
            "sig": self.sig,
        }

    def to_message(self) -> str:
        return json.dumps(
            [
                ClientMessageType.EVENT,
                self.to_dict(),
            ]
        )

    def __repr__(self):
        note_id = self.bech32()
        return f'Event({note_id[:10]}...{note_id[-10:]})'

    def __str__(self):
        return self.to_message()
