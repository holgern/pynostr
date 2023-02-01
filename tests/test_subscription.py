import json
import unittest

from pynostr.filters import Filters, FiltersList
from pynostr.message_type import ClientMessageType
from pynostr.subscription import Subscription


class TestSubscription(unittest.TestCase):
    def test_subscription_id(self):
        """check that subscription contents dump to JSON and load back to Python with
        expected types."""
        filtersList = FiltersList([Filters()])
        id = 123

        with self.assertRaisesRegex(TypeError, "Argument 'id' must be of type str"):
            subscription = Subscription(id=id, filtersList=filtersList)

        subscription = Subscription(id=str(id), filtersList=filtersList)
        request = [ClientMessageType.REQUEST, subscription.id]
        request.extend(subscription.filtersList.to_json_array())
        message = json.dumps(request)
        request_received = json.loads(message)
        message_type, subscription_id, req_filters = request_received
        self.assertTrue(isinstance(subscription_id, str))
        self.assertEqual(message_type, ClientMessageType.REQUEST)
        self.assertTrue(isinstance(req_filters, dict))
