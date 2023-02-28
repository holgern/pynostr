import logging
from dataclasses import dataclass
from typing import Optional

from .event import Event, EventKind
from .exception import NIPValidationException
from .key import PrivateKey, PublicKey

log = logging.getLogger(__name__)


@dataclass
class EncryptedDirectMessage:
    """NIP-04 Encrypted Direct Message."""

    pubkey: Optional[str] = None
    recipient_pubkey: Optional[str] = None
    cleartext_content: Optional[str] = None
    encrypted_message: Optional[str] = None
    reference_event_id: Optional[str] = None

    @classmethod
    def from_event(cls, event: Event) -> 'EncryptedDirectMessage':
        if event.kind != EventKind.ENCRYPTED_DIRECT_MESSAGE:
            return None
        dm = EncryptedDirectMessage(encrypted_message=event.content)
        dm.pubkey = event.pubkey
        dm.event = event
        return dm

    @classmethod
    def from_npub(cls, npub: str) -> 'EncryptedDirectMessage':
        dm = EncryptedDirectMessage()
        dm.pubkey = PublicKey.from_npub(npub).hex()
        return dm

    def to_event(self) -> Event:
        e = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        if self.encrypted_message is None or "?iv=" not in self.encrypted_message:
            raise NIPValidationException("Encrypted message is missing!")
        if self.recipient_pubkey is None:
            raise NIPValidationException("recipient_pubkey is missing!")
        e.content = self.encrypted_message
        e.pubkey = self.pubkey
        e.add_pubkey_ref(self.recipient_pubkey)
        if self.reference_event_id is not None:
            e.add_event_ref(self.reference_event_id)
        e.compute_id()
        return e

    def encrypt(
        self,
        private_key_hex: str,
        cleartext_content: str = None,
        recipient_pubkey: str = None,
    ) -> None:
        if cleartext_content is not None:
            self.cleartext_content = cleartext_content
        if recipient_pubkey is not None:
            self.recipient_pubkey = recipient_pubkey
        if self.recipient_pubkey is None:
            raise Exception("recipient_pubkey must not be None")
        if self.cleartext_content is None:
            raise Exception("cleartext_content must not be None")
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        self.pubkey = sk.public_key.hex()
        self.encrypted_message = sk.encrypt_message(
            message=self.cleartext_content, public_key_hex=self.recipient_pubkey
        )

    def decrypt(
        self,
        private_key_hex: str,
        encrypted_message: str = None,
        public_key_hex: str = None,
    ) -> None:
        if encrypted_message is not None:
            self.encrypted_message = encrypted_message
        if public_key_hex is None:
            public_key_hex = self.recipient_pubkey
        if public_key_hex is None:
            raise Exception("public_key must not be None")
        if self.encrypted_message is None:
            raise Exception("encrypted_message must not be None")
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        self.cleartext_content = sk.decrypt_message(
            encoded_message=self.encrypted_message, public_key_hex=public_key_hex
        )
