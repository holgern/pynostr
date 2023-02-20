import unittest

from pynostr.delegation import Delegation
from pynostr.event import Event, EventKind
from pynostr.key import PrivateKey


class TestDelegation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity_pk = PrivateKey()
        cls.delegatee_pk = PrivateKey()

    def test_event_signing(self):
        delegation = Delegation(
            delegator_pubkey=self.identity_pk.public_key.hex(),
            delegatee_pubkey=self.delegatee_pk.public_key.hex(),
            event_kind=EventKind.TEXT_NOTE,
            duration_secs=30 * 24 * 60 * 60,
        )

        self.identity_pk.sign_delegation(delegation)

        event = Event(
            "Hello, NIP-26!",
            tags=[delegation.get_tag()],
        )
        event.sign(self.delegatee_pk.hex())
        self.assertTrue(event.sig is not None)
