"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import time
import unittest

from pynostr.event import Event
from pynostr.key import PrivateKey


class TestEvent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sender_pk = PrivateKey()
        cls.sender_pubkey = cls.sender_pk.public_key.hex()

    def test_note_event(self):
        pk1 = PrivateKey.from_hex(
            "964b29795d621cdacf05fd94fb23206c88742db1fa50b34d7545f3a2221d8124"
        )
        event = Event("Hello Nostr!", pk1.public_key.hex())
        event.created_at = 1671406583
        event.compute_id()
        event.sign(pk1.hex())
        self.assertEqual(
            "23411895658d374ec922adf774a70172290b2c738ae67815bd8945e5d8fff3bb", event.id
        )
        self.assertTrue(event.verify())

    def test_event_default_time(self):
        public_key = PrivateKey().public_key.hex()
        event1 = Event(pubkey=public_key, content='test event')
        time.sleep(1.5)
        event2 = Event(pubkey=public_key, content='test event')
        self.assertTrue(event1.created_at < event2.created_at)

    def test_add_event_ref(self):
        some_event_id = "some_event_id"
        event = Event(content="Adding an 'e' tag")
        event.add_event_ref(some_event_id)
        self.assertTrue(['e', some_event_id] in event.tags)
        self.assertEqual(event.get_tag_count('e'), 1)
        self.assertEqual(event.get_tag_count('p'), 0)
        self.assertEqual(event.get_tag_list('e'), [some_event_id])
        self.assertEqual(event.get_tag_list('p'), [])
        self.assertEqual(event.get_tag_types(), ['e'])
        self.assertEqual(event.get_tag_dict(), {"e": [some_event_id]})
        self.assertTrue(event.has_event_ref(some_event_id))

    def test_add_pubkey_ref(self):
        some_pubkey = "some_pubkey"
        event = Event(content="Adding a 'p' tag")
        event.add_pubkey_ref(some_pubkey)
        self.assertTrue(['p', some_pubkey] in event.tags)
        self.assertEqual(event.get_tag_count('p'), 1)
        self.assertEqual(event.get_tag_count('e'), 0)
        self.assertEqual(event.get_tag_list('p'), [some_pubkey])
        self.assertEqual(event.get_tag_list('e'), [])
        self.assertEqual(event.get_tag_types(), ['p'])
        self.assertEqual(event.get_tag_dict(), {"p": [some_pubkey]})
        self.assertTrue(event.has_pubkey_ref(some_pubkey))

    def test_sign_event_is_valid(self):
        """Sign should create a signature that can be verified against Event.id."""
        event = Event(content="Hello, world!")
        event.sign(self.sender_pk.hex())
        self.assertTrue(event.verify())

    def test_sign_event_adds_pubkey(self):
        """Sign should add the sender's pubkey if not already specified."""
        event = Event(content="Hello, world!")

        # The event's public_key hasn't been specified yet
        self.assertTrue(event.pubkey is None)
        event.sign(self.sender_pk.hex())

        # PrivateKey.sign() should have populated public_key
        self.assertEqual(event.pubkey, self.sender_pubkey)

    def test_dict_roundtrip(self):
        """Conversion to dict and back result in same object."""
        event = Event(
            content='test event',
            created_at=12345678,
            kind=1,
        )
        event.add_pubkey_ref("some_pubkey")

        got = Event.from_dict(event.to_dict())
        self.assertEqual(got, event)
