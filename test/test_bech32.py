import binascii
import unittest

import tlv8

from pynostr.bech32 import bech32_decode, bech32_encode


class TestBech32(unittest.TestCase):
    def test_npub(self):
        npub = "npub180cvv07tjdrrgpa0j7j7tmnyl2yr6yr7l8j4s3evf6u64th6gkwsyjh6w6"
        pub_key = "3bf0c63fcb93463407af97a5e5ee64fa883d107ef9e558472c4eb9aaaefa459d"
        self.assertEqual(bytes(bech32_decode(npub)).hex(), pub_key)
        self.assertEqual(bech32_encode(binascii.unhexlify(pub_key), "npub"), npub)

    def test_nsec(self):
        npub = "nsec180cvv07tjdrrgpa0j7j7tmnyl2yr6yr7l8j4s3evf6u64th6gkwsgyumg0"
        pub_key = "3bf0c63fcb93463407af97a5e5ee64fa883d107ef9e558472c4eb9aaaefa459d"
        self.assertEqual(bytes(bech32_decode(npub)).hex(), pub_key)
        self.assertEqual(bech32_encode(binascii.unhexlify(pub_key), "nsec"), npub)

    def test_nprofile(self):
        nprofile = (
            "nprofile1qqsrhuxx8l9ex335q7he0f09aej04zpazpl0ne2cgukyaw"
            + "d24mayt8gpp4mhxue69uhhytnc9e3k7mgpz4mhxue69uhkg6nzv9e"
            + "juumpv34kytnrdaksjlyr9p"
        )
        pub_key = "3bf0c63fcb93463407af97a5e5ee64fa883d107ef9e558472c4eb9aaaefa459d"
        relay1 = "wss://r.x.com"
        relay2 = "wss://djbas.sadkb.com"
        decode = bytes(bech32_decode(nprofile))

        data = tlv8.deep_decode(decode)
        self.assertEqual(data[0].type_id, 0)
        self.assertEqual(binascii.hexlify(data[0].data).decode(), pub_key)

        self.assertEqual(data[1].type_id, 1)
        self.assertEqual(data[1].data.decode(), relay1)

        self.assertEqual(data[2].type_id, 1)
        self.assertEqual(data[2].data.decode(), relay2)

        structure = [
            tlv8.Entry(0, binascii.unhexlify(pub_key)),
            tlv8.Entry(1, relay1.encode()),
            tlv8.Entry(1, relay2.encode()),
        ]
        bytes_data = tlv8.encode(structure)

        bytes_data = b''
        for entry in structure:
            bytes_data += entry.encode()

        self.assertEqual(bech32_encode(bytes_data, "nprofile"), nprofile)
