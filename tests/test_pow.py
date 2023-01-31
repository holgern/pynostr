import unittest

from pynostr import pow
from pynostr.event import Event, EventKind
from pynostr.key import PrivateKey
from pynostr.pow import Pow, PowEvent, PowKey, PowVanityKey


class TestPow(unittest.TestCase):
    def test_count_leading_zero(self):
        self.assertEqual(pow.count_leading_zero_bits("048d"), 5)
        self.assertEqual(pow.count_leading_zero_bits("ffff"), 0)

    def test_mine_event(self):
        """Test mining an event with specific difficulty."""
        public_key = PrivateKey().public_key.hex()
        difficulty = 8
        event = Event(content='test', pubkey=public_key, kind=EventKind.TEXT_NOTE)
        p = PowEvent(difficulty, event)
        event = p.mine()
        self.assertTrue(pow.count_leading_zero_bits(event.id) >= difficulty)

    def test_mine_key(self):
        """Test mining a public key with specific difficulty."""
        difficulty = 8
        p = PowKey(difficulty)
        sk = p.mine()
        self.assertTrue(pow.count_leading_zero_bits(sk.public_key.hex()) >= difficulty)

    def test_time_estimates(self):
        """Test functions to estimate POW time."""
        public_key = PrivateKey().public_key.hex()
        event = Event(content='test', pubkey=public_key, kind=EventKind.TEXT_NOTE)
        p = PowEvent(8, event)
        # test successful run of all estimators
        p.get_expected_time()
        p_key = PowKey(8)
        p_key.get_expected_time()
        p_vkey = PowVanityKey("t")
        p_vkey.get_expected_time()

    def test_mine_vanity_key(self):
        """Test vanity key mining."""
        pattern = '23'
        p = PowVanityKey(pattern)
        sk = p.mine()
        sk.public_key.bech32()
        self.assertTrue(sk.public_key.bech32().startswith(f'npub1{pattern}'))

        p = PowVanityKey(suffix=pattern)
        sk = p.mine()
        self.assertTrue(sk.public_key.bech32().endswith(pattern))

        # mine an invalid pattern
        pattern = '1'

        with self.assertRaisesRegex(ValueError, "not in valid list of bech32 chars"):
            p = PowVanityKey(pattern)

    def test_expected_pow_guesses(self):
        p = Pow()
        p.n_pattern = 32
        p.n_options = 2
        e1 = p.get_expected_guesses()

        p.n_pattern = 8
        p.n_options = 16
        e2 = p.get_expected_guesses()
        self.assertEqual(e1, e2)
