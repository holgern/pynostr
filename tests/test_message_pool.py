import json
import unittest
import uuid
import time
from pynostr.event import Event, EventKind
from pynostr.message_pool import MessagePool
from pynostr.filters import FiltersList, Filters

class TestMessagePool(unittest.TestCase):
    def test_empty_pool(self):
        mp = MessagePool()
        self.assertEqual(mp.has_events(), 0)
        self.assertEqual(mp.has_notices(), 0)
        self.assertEqual(mp.has_eose_notices(), 0)

    def test_notices(self):
        mp = MessagePool()
        url = "ws://relay"
        mp.add_message('["NOTICE", "Test Notice"]', url)
        self.assertEqual(mp.has_events(), 0)
        self.assertEqual(mp.has_notices(), 1)
        self.assertEqual(mp.has_eose_notices(), 0)
        results = mp.get_all()["notices"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)
        self.assertEqual(results[0].content, "Test Notice")
        mp.add_message('["NOTICE", "Test Notice"]', url)
        results = mp.get_all_notices()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)
        self.assertEqual(results[0].content, "Test Notice")

    def test_eose(self):
        mp = MessagePool()
        url = "ws://relay"
        mp.add_message(json.dumps(["EOSE", uuid.uuid1().hex]), url)
        self.assertEqual(mp.has_events(), 0)
        self.assertEqual(mp.has_notices(), 0)
        self.assertEqual(mp.has_eose_notices(), 1)
        results = mp.get_all()["eose"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)
        mp.add_message(json.dumps(["EOSE", uuid.uuid1().hex]), url)
        results = mp.get_all_eose()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)

    def test_event(self):
        mp = MessagePool()
        e = Event()
        url = "ws://relay"
        mp.add_message(json.dumps(["EVENT", uuid.uuid1().hex, e.to_dict()]), url)
        self.assertEqual(mp.has_events(), 1)
        self.assertEqual(mp.has_notices(), 0)
        self.assertEqual(mp.has_eose_notices(), 0)
        results = mp.get_all()["events"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)
        mp.add_message(json.dumps(["EVENT", uuid.uuid1().hex, e.to_dict()]), url)
        results = mp.get_all_events()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, url)

    def test_count(self):
        mp = MessagePool()
        filters = FiltersList([Filters(kinds=[EventKind.TEXT_NOTE], until=time.time_ns())]).to_json_array()
        url = "ws://relay"

        sub_id = uuid.uuid1().hex
        mp.add_message(json.dumps(["COUNT", sub_id, filters]), url)
        self.assertEqual(mp.has_counts(), 1)
        results = mp.get_all()["count"]
        self.assertEqual(results[0].subscription_id, sub_id)
        self.assertEqual(len(results), 1)
