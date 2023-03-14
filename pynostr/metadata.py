import json
import logging
from dataclasses import dataclass
from typing import List, Optional

from .event import Event, EventKind
from .key import PublicKey
from .utils import extract_nip05

log = logging.getLogger(__name__)


@dataclass
class MetadataIdentity:
    """Nip-39 Identity.

    :param claim_type: str
    :param identity: str
    :param proof: str
    """

    claim_type: str
    identity: str
    proof: str

    @classmethod
    def from_list(cls, lst: list) -> 'MetadataIdentity':
        return MetadataIdentity(
            claim_type=lst[0].split(":")[0], identity=lst[0].split(":")[1], proof=lst[1]
        )

    def to_list(self):
        return [f"{self.claim_type}:{self.identity}", self.proof]


@dataclass
class Metadata(Event):
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
    identities: Optional[List[MetadataIdentity]] = None

    def __post_init__(self):
        Event.__post_init__(self)
        self.kind = EventKind.SET_METADATA
        if self.identities is None:
            self.identities = []

    @classmethod
    def from_dict(cls, msg: dict) -> 'Metadata':
        # "id" is ignore, as it will be computed from the contents
        m = Metadata(
            content=msg['content'],
            pubkey=msg['pubkey'],
            created_at=msg['created_at'],
            kind=EventKind.SET_METADATA,
            tags=msg['tags'],
            sig=msg['sig'],
        )
        if m.content is not None and bool(m.content.strip()):
            m.set_metadata(json.loads(m.content))
        m.set_identities_from_tags()
        return m

    @classmethod
    def from_event(cls, event: Event) -> 'Metadata':
        event_dict = event.to_dict()
        m = Metadata(
            content=event_dict['content'],
            pubkey=event_dict['pubkey'],
            created_at=event_dict['created_at'],
            kind=EventKind.SET_METADATA,
            tags=event_dict['tags'],
            sig=event_dict['sig'],
        )
        if (
            m.content is not None
            and bool(m.content.strip())
            and event.kind == EventKind.SET_METADATA
        ):
            m.set_metadata(json.loads(m.content))
        m.set_identities_from_tags()
        return m

    def set_identities_from_tags(self):
        if self.identities is None:
            self.identities = []
        else:
            self.identities.clear()
        if self.get_tag_count("i") > 0:
            for tag in self.get_tag_list("i"):
                identity = MetadataIdentity.from_list(tag)
                self.identities.append(identity)

    def set_tags_from_identities(self):
        self.clear_tags("i")
        if self.identities and len(self.identities) > 0:
            for identity in self.identities:
                tag = identity.to_list()
                self.add_tag("i", tag)

    def to_event(self) -> Event:
        self.update()
        return Event.from_dict(self.to_dict())

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

    def update(self):
        self.content = json.dumps(self.metadata_to_dict())
        self.set_tags_from_identities()
        self.compute_id()

    def metadata_to_dict(self) -> dict:
        ret = {}
        if self.name:
            ret["name"] = self.name
        if self.about:
            ret["about"] = self.about
        if self.nip05:
            ret["nip05"] = self.nip05
        if self.picture:
            ret["picture"] = self.picture
        if self.banner:
            ret["banner"] = self.banner
        if self.lud16:
            ret["lud16"] = self.lud16
        if self.lud06:
            ret["lud06"] = self.lud06
        if self.username:
            ret["username"] = self.username
        if self.display_name:
            ret["display_name"] = self.display_name
        if self.website:
            ret["website"] = self.website
        if self.addional:
            ret.update(self.addional)
        return ret

    def set_metadata(self, msg) -> None:
        if "name" in msg:
            self.name = msg.pop("name")
        if "about" in msg:
            self.about = msg.pop("about")
        if "nip05" in msg:
            self.nip05 = msg.pop("nip05")
        if "picture" in msg:
            self.picture = msg.pop("picture")
        if "banner" in msg:
            self.banner = msg.pop("banner")
        if "lud16" in msg:
            self.lud16 = msg.pop("lud16")
        if "lud06" in msg:
            self.lud06 = msg.pop("lud06")
        if "username" in msg:
            self.username = msg.pop("username")
        if "display_name" in msg:
            self.display_name = msg.pop("display_name")
        if "website" in msg:
            self.website = msg.pop("website")
        if len(msg) > 0:
            self.addional = msg

    def sign(self, private_key_hex: str) -> None:
        self.update()
        return Event.sign(self, private_key_hex)

    def to_dict(self) -> dict:
        self.update()
        ret = Event.to_dict(self)
        return ret

    def to_message(self) -> str:
        return Event.to_message(self)
