"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import time
import unittest

from pynostr.event import Event, EventKind
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
        self.assertTrue(event.has_event_ref(some_event_id))

    def test_add_pubkey_ref(self):
        some_pubkey = "some_pubkey"
        event = Event(content="Adding a 'p' tag")
        event.add_pubkey_ref(some_pubkey)
        self.assertTrue(['p', some_pubkey] in event.tags)
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


class TestEncryptedDirectMessage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sender_pk = PrivateKey.from_hex(
            "29307c4354b7d9d311d2cec4878c0de56c93a921d300273c19577e9004de3c9f"
        )
        cls.sender_pubkey = cls.sender_pk.public_key.hex()
        cls.recipient_pk = PrivateKey.from_hex(
            "4138d1b6dde34f81c38cef2630429e85847dd5b70508e37f53c844f66f19f983"
        )
        cls.recipient_pubkey = cls.recipient_pk.public_key.hex()

    def test_content_field_not_allowed(self):
        """Should not let users instantiate a new DM with `content` field data."""
        with self.assertRaisesRegex(Exception, "cannot use"):
            Event(content="My message!", kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)

    def test_recipient_p_tag(self):
        """Should generate recipient 'p' tag."""
        dm = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content="Secret message!",
        )
        assert ['p', self.recipient_pubkey] in dm.tags

    def test_encrypt_dm(self):
        """Should encrypt a DM and populate its `content` field with ciphertext that
        either party can decrypt."""
        message1 = "Test"
        message2 = "Test2"
        message3 = "Test3"
        message4 = "Test4"

        dm1 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        self.assertTrue(dm1.content is None)
        dm1.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message1,
        )
        dm2 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm2.encrypt_dm(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message2,
        )
        dm3 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm3.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message3,
        )
        dm4 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm4.encrypt_dm(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message4,
        )

        # After encrypting, the content field should now be populated
        self.assertTrue(dm1.content is not None)

        # Sender should be able to decrypt
        decm1_sender = self.sender_pk.decrypt_message(
            encoded_message=dm1.content, public_key_hex=self.recipient_pubkey
        )
        decm2_sender = self.sender_pk.decrypt_message(
            encoded_message=dm2.content, public_key_hex=self.recipient_pubkey
        )
        decm3_sender = self.sender_pk.decrypt_message(
            encoded_message=dm3.content, public_key_hex=self.recipient_pubkey
        )
        decm4_sender = self.sender_pk.decrypt_message(
            encoded_message=dm4.content, public_key_hex=self.recipient_pubkey
        )

        decm1_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm1.content, public_key_hex=self.sender_pubkey
        )
        decm2_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm2.content, public_key_hex=self.sender_pubkey
        )
        decm3_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm3.content, public_key_hex=self.sender_pubkey
        )
        decm4_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm4.content, public_key_hex=self.sender_pubkey
        )
        self.assertEqual(message1, decm1_receiver)
        self.assertEqual(message1, decm1_sender)
        self.assertEqual(message2, decm2_receiver)
        self.assertEqual(message2, decm2_sender)
        self.assertEqual(message3, decm3_receiver)
        self.assertEqual(message3, decm3_sender)
        self.assertEqual(message4, decm4_receiver)
        self.assertEqual(message4, decm4_sender)

    def test_decrypt_dm(self):
        message1 = "Test"
        message2 = "Test2"
        message3 = "Test3"
        message4 = "Test4"
        encrypt1 = "VOqWLiW4wv8+fDsNC00a1w==?iv=LSIH1sk13Mw09PV8Z80sag=="
        encrypt2 = "abZBRLPta8888xDkg6pUWA==?iv=Gj5KOUbFqREhSdbMENRKEg=="
        encrypt3 = "w2AsXNN0EysjG6/E/GZWPg==?iv=3c7qsPxSOckGeqjjpwQQ4A=="
        encrypt4 = "nBfP5P2GEEOlfNYMoxADDg==?iv=VsFd7eE8BfoyDJpfQ7kjhQ=="

        dm_s1 = self.sender_pk.decrypt_message(
            encoded_message=encrypt1, public_key_hex=self.recipient_pubkey
        )
        dm_s2 = self.sender_pk.decrypt_message(
            encoded_message=encrypt2, public_key_hex=self.recipient_pubkey
        )
        dm_s3 = self.sender_pk.decrypt_message(
            encoded_message=encrypt3, public_key_hex=self.recipient_pubkey
        )
        dm_s4 = self.sender_pk.decrypt_message(
            encoded_message=encrypt4, public_key_hex=self.recipient_pubkey
        )
        self.assertEqual(dm_s1, message1)
        self.assertEqual(dm_s2, message2)
        self.assertEqual(dm_s3, message3)
        self.assertEqual(dm_s4, message4)

        dm_r1 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt1, public_key_hex=self.sender_pubkey
        )
        dm_r2 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt2, public_key_hex=self.sender_pubkey
        )
        dm_r3 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt3, public_key_hex=self.sender_pubkey
        )
        dm_r4 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt4, public_key_hex=self.sender_pubkey
        )
        self.assertEqual(dm_r1, message1)
        self.assertEqual(dm_r2, message2)
        self.assertEqual(dm_r3, message3)
        self.assertEqual(dm_r4, message4)

    def test_sign_encrypts_dm(self):
        """`sign` should encrypt a DM that hasn't been encrypted yet."""
        dm = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        self.assertTrue(dm.content is None)
        dm.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content="Some DM message",
        )

        dm.sign(self.sender_pk.hex())

        self.assertTrue(dm.content is not None)

    def test_shared_secret(self):
        sender_pk = "29307c4354b7d9d311d2cec4878c0de56c93a921d300273c19577e9004de3c9f"
        recipient_pk = (
            "4138d1b6dde34f81c38cef2630429e85847dd5b70508e37f53c844f66f19f983"
        )

        sender_pubkey = PrivateKey.from_hex(sender_pk).public_key.hex()
        recipient_pubkey = PrivateKey.from_hex(recipient_pk).public_key.hex()

        shared_secret1 = PrivateKey.from_hex(sender_pk).compute_shared_secret(
            recipient_pubkey
        )
        shared_secret2 = PrivateKey.from_hex(recipient_pk).compute_shared_secret(
            sender_pubkey
        )
        self.assertEqual(shared_secret1, shared_secret2)

    def test_decrypt_event(self):
        dm1 = Event.from_dict(
            {
                "id": "46c76ec67d03babdb840254b3667585143cc499497b0a6a40aedc9ce2de416"
                "70",
                "pubkey": "f3c25355c29f64ea8e9b4e11b583ac0a7d0d8235f156cffec2b73e5756a"
                "ab206",
                "created_at": 1674819397,
                "kind": 4,
                "tags": [
                    [
                        "p",
                        "a1db8e8b047e1350958a55e0a853151d0e1f685fa5cf3772e01bccc5aa5c"
                        "b2eb",
                    ]
                ],
                "content": "VOqWLiW4wv8+fDsNC00a1w==?iv=LSIH1sk13Mw09PV8Z80sag==",
                "sig": "982e825d32e78bf695a2511e14d2958e0d480bfa338e12307e5eb7ecad3b"
                "d86d53c2d508df9083a0fc25b44c44ae4c622f7405bbc2ca723c5dbc98da48214f16",
            }
        )
        self.assertTrue(dm1.verify())
