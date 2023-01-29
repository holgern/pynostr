import unittest
from os import urandom

from pynostr.key import PrivateKey, PublicKey


class TestPrivateKey(unittest.TestCase):
    def test_eq_true(self):
        """__eq__ should return True when PrivateKeys are equal."""
        pk1 = PrivateKey()
        pk2 = PrivateKey(pk1.raw_secret)
        self.assertEqual(pk1, pk2)

    def test_eq_false(self):
        """__eq__ should return False when PrivateKeys are not equal."""
        pk1 = PrivateKey()
        pk2 = PrivateKey()
        self.assertNotEqual(pk1.raw_secret, pk2.raw_secret)
        self.assertNotEqual(pk1, pk2)

    def test_from_nsec(self):
        """PrivateKey.from_nsec should yield the source's raw_secret."""
        pk1 = PrivateKey()
        pk2 = PrivateKey.from_nsec(pk1.bech32())
        self.assertEqual(pk1.raw_secret, pk2.raw_secret)

    def test_from_hex(self):
        pk1 = PrivateKey()
        pk2 = PrivateKey.from_hex(pk1.hex())
        self.assertEqual(pk1.raw_secret, pk2.raw_secret)

    def test_from_hex2(self):
        pk1 = PrivateKey.from_hex(
            "964b29795d621cdacf05fd94fb23206c88742db1fa50b34d7545f3a2221d8124"
        )
        pub1 = PublicKey(pk1)
        self.assertEqual(
            pub1.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )

        pub1 = PublicKey(
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81"
        )
        self.assertEqual(
            pub1.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )

        pub1 = PublicKey(
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81"
        )
        self.assertEqual(
            pub1.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )
        self.assertEqual(
            pk1.public_key.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )
        self.assertEqual(
            pk1.bech32(),
            "nsec1je9jj72avgwd4nc9lk20kgeqdjy8gtd3lfgtxnt4ghe6ygsasyjq7kh6c4",
        )
        self.assertEqual(
            pub1.bech32(),
            "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p",
        )

    def test_from_nsec2(self):
        pk1 = PrivateKey.from_nsec(
            "nsec1je9jj72avgwd4nc9lk20kgeqdjy8gtd3lfgtxnt4ghe6ygsasyjq7kh6c4"
        )
        pub1 = PublicKey(pk1)
        self.assertEqual(
            pub1.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )
        self.assertEqual(
            pk1.bech32(),
            "nsec1je9jj72avgwd4nc9lk20kgeqdjy8gtd3lfgtxnt4ghe6ygsasyjq7kh6c4",
        )
        self.assertEqual(
            pub1.bech32(),
            "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p",
        )

    def test_pubkey_from_nsec(self):
        pub1 = PublicKey.from_npub(
            "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p"
        )
        self.assertEqual(
            pub1.hex(),
            "da15317263858ad496a21c79c6dc5f5cf9af880adf3a6794dbbf2883186c9d81",
        )
        self.assertEqual(
            pub1.bech32(),
            "npub1mg2nzunrsk9df94zr3uudhzltnu6lzq2muax09xmhu5gxxrvnkqsvpjg3p",
        )

    def test_schnorr_signature(self):
        private_key = PrivateKey()
        message = urandom(32)
        sig = private_key.sign(message, urandom(32))
        self.assertTrue(private_key.public_key.verify(sig, message))
        sig = private_key.sign(message)
        self.assertTrue(private_key.public_key.verify(sig, message))

    def test_shared_secret(self):
        sender_pk = "29307c4354b7d9d311d2cec4878c0de56c93a921d300273c19577e9004de3c9f"
        recipient_pk = (
            "4138d1b6dde34f81c38cef2630429e85847dd5b70508e37f53c844f66f19f983"
        )
        recipient_pub = (
            "a1db8e8b047e1350958a55e0a853151d0e1f685fa5cf3772e01bccc5aa5cb2eb"
        )
        sender_pub = "f3c25355c29f64ea8e9b4e11b583ac0a7d0d8235f156cffec2b73e5756aab206"

        sender_pubkey = PrivateKey.from_hex(sender_pk).public_key.hex()
        recipient_pubkey = PrivateKey.from_hex(recipient_pk).public_key.hex()
        self.assertEqual(sender_pubkey, sender_pub)
        self.assertEqual(recipient_pubkey, recipient_pub)

        shared_secret1 = PrivateKey.from_hex(sender_pk).compute_shared_secret(
            recipient_pub
        )
        shared_secret2 = PrivateKey.from_hex(recipient_pk).compute_shared_secret(
            sender_pub
        )
        self.assertEqual(
            shared_secret1.hex(),
            '646570d4716e0c7e4106788f113a410d5b647225dca3b47ef98bedb64c8044e1',
        )
        self.assertEqual(
            shared_secret2.hex(),
            '646570d4716e0c7e4106788f113a410d5b647225dca3b47ef98bedb64c8044e1',
        )
