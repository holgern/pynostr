import json
import logging
from dataclasses import dataclass
from typing import List, Optional

from .event import Event, EventKind
from .key import PublicKey
from .utils import extract_nip05

log = logging.getLogger(__name__)


@dataclass
class Metadata:
    pubkey: Optional[str] = None
    name: Optional[str] = None
    about: Optional[str] = None
    nip05: Optional[str] = None
    picture: Optional[str] = None
    banner: Optional[str] = None
    lud16: Optional[str] = None
    lud06: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    website: Optional[str] = None
    addional: Optional[dict] = None
    event: Optional[Event] = None
    relays: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, msg: dict) -> 'Metadata':
        # "id" is ignore, as it will be computed from the contents
        p = Metadata()
        if "name" in msg:
            p.name = msg.pop("name")
        if "about" in msg:
            p.about = msg.pop("about")
        if "nip05" in msg:
            p.nip05 = msg.pop("nip05")
        if "picture" in msg:
            p.picture = msg.pop("picture")
        if "banner" in msg:
            p.banner = msg.pop("banner")
        if "lud16" in msg:
            p.lud16 = msg.pop("lud16")
        if "lud06" in msg:
            p.lud06 = msg.pop("lud06")
        if "username" in msg:
            p.username = msg.pop("username")
        if "display_name" in msg:
            p.display_name = msg.pop("display_name")
        if "website" in msg:
            p.website = msg.pop("website")
        if len(msg) > 0:
            p.addional = msg
        return p

    @classmethod
    def from_event(cls, event: Event) -> 'Metadata':
        if event.kind != EventKind.SET_METADATA:
            return None
        metadata = json.loads(event.content)
        m = Metadata.from_dict(metadata)
        m.pubkey = event.pubkey
        m.event = event
        return m

    @classmethod
    def from_nip05(cls, nip05: str) -> 'Metadata':
        m = Metadata()
        m.nip05 = nip05
        try:
            pubkey, relays = extract_nip05(nip05)
        except Exception:
            return m
        if pubkey is not None:
            m.pubkey = pubkey
        if relays is not None:
            m.relays = relays
        return m

    @classmethod
    def from_npub(cls, npub: str) -> 'Metadata':
        m = Metadata()
        m.pubkey = PublicKey.from_npub(npub).hex()
        return m

    def validate_nip05(self):
        if self.nip05 is None or self.pubkey is None:
            return False
        try:
            pubkey, relays = extract_nip05(self.nip05)
        except Exception:
            return False
        if pubkey is not None:
            if pubkey == self.pubkey:
                return True

        return False
