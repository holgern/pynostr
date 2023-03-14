import unittest

from pynostr.base_relay import BaseRelay, RelayPolicy
from pynostr.relay_list import RelayList


class TestRelayList(unittest.TestCase):
    def setUp(self):
        self.rl = RelayList()

    def test_len(self):
        self.assertEqual(len(self.rl), 0)

    def test_append_relay(self):
        relay = BaseRelay("ws://testurl.com", RelayPolicy())
        self.rl.append_relay(relay)
        self.assertEqual(len(self.rl), 1)

    def test_append_url_list(self):
        url_list = ["ws://testurl1.com", "ws://testurl2.com"]
        policy = RelayPolicy()
        self.rl.append_url_list(url_list, policy)
        self.assertEqual(len(self.rl), 2)
