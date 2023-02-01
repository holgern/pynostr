import json
import unittest

from pynostr.filters import Filters, FiltersList
from pynostr.message_type import ClientMessageType
from pynostr.request import Request
from pynostr.subscription import Subscription


class TestRequest(unittest.TestCase):
    def test_request_id(self):
        """check that request contents dump to JSON and load back to Python with
        expected types."""
        filtersList = FiltersList([Filters()])
        id = 123

        subscription = Subscription(id=str(id), filtersList=filtersList)

        request = Request(subscription.id, filtersList)

        request_received = json.loads(request.to_message())
        message_type, subscription_id, req_filters = request_received
        self.assertTrue(isinstance(subscription_id, str))
        self.assertEqual(message_type, ClientMessageType.REQUEST)
        self.assertTrue(isinstance(req_filters, dict))
