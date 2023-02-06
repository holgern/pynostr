"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import unittest

from pynostr.event import Event
from pynostr.filters import FiltersList
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayException, RelayManager
from pynostr.subscription import Subscription


class TestPrivateKey(unittest.TestCase):
    def test_only_relay_valid_events(self):
        """publish_event raise a RelayException if an Event fails verification."""
        pk = PrivateKey()
        event = Event(
            pubkey=pk.public_key.hex(),
            content="Hello, world!",
        )

        relay_manager = RelayManager()

        # Deliberately forget to sign the Event
        with self.assertRaisesRegex(RelayException, "must be signed"):
            relay_manager.publish_event(event)

        # Attempt to relay with a nonsense signature
        event.sig = (b'\00' * 64).hex()
        with self.assertRaisesRegex(RelayException, "failed to verify"):
            relay_manager.publish_event(event)

        # Properly signed Event can be relayed
        event.sign(pk.hex())
        relay_manager.publish_event(event)

    def test_separate_subscriptions(self):
        """make sure that subscription dictionary default is not the same object across
        all relays so that subscriptions can vary."""
        # initiate relay manager with two relays
        relay_manager = RelayManager(error_threshold=1)
        relay_manager.add_relay(url='ws://fake-relay1')
        relay_manager.add_relay(url='ws://fake-relay2')

        # make test subscription and add to one relay
        test_subscription = Subscription('test', FiltersList())
        relay_manager.relays['ws://fake-relay1'].subscriptions.update(
            {test_subscription.id: test_subscription}
        )
        # make sure test subscription isn't in second relay subscriptions
        self.assertTrue(
            test_subscription.id
            not in relay_manager.relays['ws://fake-relay2'].subscriptions.keys()
        )
        relay_manager.close_all_relay_connections()
