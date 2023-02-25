import unittest

from pynostr.encrypted_dm import EncryptedDirectMessage
from pynostr.event import Event
from pynostr.key import PrivateKey


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

    def test_recipient_p_tag(self):
        """Should generate recipient 'p' tag."""
        dm = EncryptedDirectMessage()
        dm.encrypt(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content="Secret message!",
        )
        assert ['p', self.recipient_pubkey] in dm.to_event().tags

    def test_encrypt_dm(self):
        """Should encrypt a DM and populate its `content` field with ciphertext that
        either party can decrypt."""
        message1 = "Test"
        message2 = "Test2"
        message3 = "Test3"
        message4 = "Test4"

        dm1 = EncryptedDirectMessage()
        dm1.encrypt(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message1,
        )
        dm2 = EncryptedDirectMessage()
        dm2.encrypt(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message2,
        )
        dm3 = EncryptedDirectMessage()
        dm3.encrypt(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message3,
        )
        dm4 = EncryptedDirectMessage()
        dm4.encrypt(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message4,
        )
        dm1_event = dm1.to_event()
        dm2_event = dm2.to_event()
        dm3_event = dm3.to_event()
        dm4_event = dm4.to_event()

        # After encrypting, the content field should now be populated
        self.assertTrue(dm1_event.content is not None)

        # Sender should be able to decrypt
        decm1_sender = self.sender_pk.decrypt_message(
            encoded_message=dm1_event.content, public_key_hex=self.recipient_pubkey
        )
        decm2_sender = self.sender_pk.decrypt_message(
            encoded_message=dm2_event.content, public_key_hex=self.recipient_pubkey
        )
        decm3_sender = self.sender_pk.decrypt_message(
            encoded_message=dm3_event.content, public_key_hex=self.recipient_pubkey
        )
        decm4_sender = self.sender_pk.decrypt_message(
            encoded_message=dm4_event.content, public_key_hex=self.recipient_pubkey
        )

        decm1_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm1_event.content, public_key_hex=self.sender_pubkey
        )
        decm2_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm2_event.content, public_key_hex=self.sender_pubkey
        )
        decm3_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm3_event.content, public_key_hex=self.sender_pubkey
        )
        decm4_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm4_event.content, public_key_hex=self.sender_pubkey
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

        dm1 = EncryptedDirectMessage(encrypted_message=encrypt1)
        dm2 = EncryptedDirectMessage(encrypted_message=encrypt2)
        dm3 = EncryptedDirectMessage(encrypted_message=encrypt3)
        dm4 = EncryptedDirectMessage(encrypted_message=encrypt4)
        dm1.decrypt(self.sender_pk.hex(), public_key_hex=self.recipient_pubkey)
        dm2.decrypt(self.sender_pk.hex(), public_key_hex=self.recipient_pubkey)
        dm3.decrypt(self.sender_pk.hex(), public_key_hex=self.recipient_pubkey)
        dm4.decrypt(self.sender_pk.hex(), public_key_hex=self.recipient_pubkey)

        self.assertEqual(dm1.cleartext_content, message1)
        self.assertEqual(dm2.cleartext_content, message2)
        self.assertEqual(dm3.cleartext_content, message3)
        self.assertEqual(dm4.cleartext_content, message4)

        dm1.cleartext_content = None
        dm2.cleartext_content = None
        dm3.cleartext_content = None
        dm4.cleartext_content = None

        dm1.decrypt(self.recipient_pk.hex(), public_key_hex=self.sender_pubkey)
        dm2.decrypt(self.recipient_pk.hex(), public_key_hex=self.sender_pubkey)
        dm3.decrypt(self.recipient_pk.hex(), public_key_hex=self.sender_pubkey)
        dm4.decrypt(self.recipient_pk.hex(), public_key_hex=self.sender_pubkey)

        self.assertEqual(dm1.cleartext_content, message1)
        self.assertEqual(dm2.cleartext_content, message2)
        self.assertEqual(dm3.cleartext_content, message3)
        self.assertEqual(dm4.cleartext_content, message4)

    def test_sign_encrypts_dm(self):
        """`sign` should encrypt a DM that hasn't been encrypted yet."""
        dm = EncryptedDirectMessage()
        self.assertTrue(dm.cleartext_content is None)
        self.assertTrue(dm.encrypted_message is None)
        dm.encrypt(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content="Some DM message",
        )
        dm_event = dm.to_event()
        dm_event.sign(self.sender_pk.hex())

        self.assertTrue(dm_event.content is not None)

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
