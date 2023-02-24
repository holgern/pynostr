import unittest

from pynostr.base_relay import BaseRelay
from pynostr.message_pool import MessagePool


class TestBaseRelay(unittest.TestCase):
    def test_valid_message(self):
        message_pool = MessagePool()
        b = BaseRelay("wss://test.test", message_pool)
        message = (
            '["OK","fafb7406c6245e3a259b51aa6eccb9433fd765af2302ea80738f4ad8ce2'
            '2e55e",false,"blocked: not on white-list"]'
        )
        self.assertTrue(b._is_valid_message(message))

        b._on_message(message)
        self.assertTrue(message_pool.has_ok_notices())
