"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import unittest

from pynostr.event import Event, EventKind
from pynostr.key import PrivateKey
from pynostr.metadata import Metadata, MetadataIdentity


class TestMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sender_pk = PrivateKey()
        cls.sender_pubkey = cls.sender_pk.public_key.hex()

    def test_dict_roundtrip(self):
        event = Event(
            content='test event',
            created_at=12345678,
            kind=1,
        )
        metadata = Metadata.from_event(event)
        metadata.name = "test"
        metadata.update()

        got = Metadata.from_dict(metadata.to_dict())
        self.assertEqual(got, metadata)

    def test_event_roundtrip(self):
        event = Event(
            content="",
            kind=EventKind.SET_METADATA,
            created_at=12345678,
        )
        metadata = Metadata.from_event(event)
        metadata.name = "test"
        metadata.identities.append(MetadataIdentity("a", "b", "c"))
        metadata.update()

        got = Metadata.from_event(metadata.to_event())
        self.assertEqual(got.to_dict(), metadata.to_dict())
