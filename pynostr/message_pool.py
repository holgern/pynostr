"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import datetime
import json
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import List, Optional

from .event import Event
from .message_type import RelayMessageType


@dataclass
class EventMessage:
    event: str
    subscription_id: str
    url: str

    def __repr__(self):
        return f'EventMessage({self.url}: kind {str(self.event.kind)})'


@dataclass
class NoticeMessage:
    content: str
    url: str

    def __repr__(self):
        return f'Notice({self.url}: {self.content})'


@dataclass
class OKMessage:
    event_id: str
    ok: str
    message: str
    url: str

    def __repr__(self):
        return f'OK({self.url}: {self.event_id} {self.ok} {self.message})'


@dataclass
class EndOfStoredEventsMessage:
    subscription_id: str
    url: str

    def __repr__(self):
        return f'EOSE({self.url})'


class MessagePool:
    def __init__(self, first_response_only: bool = False):
        self.first_response_only = first_response_only
        self.events: Queue[EventMessage] = Queue()
        self.notices: Queue[NoticeMessage] = Queue()
        self.eose_notices: Queue[EndOfStoredEventsMessage] = Queue()
        self.ok_notices: Queue[OKMessage] = Queue()
        self._unique_objects: set = set()
        self.lock: Lock = Lock()

    def add_message(self, message: str, url: str):
        self._process_message(message, url)

    def get_all_events(self):
        events = []
        while self.has_events():
            events.append(self.get_event())
        return events

    def get_all_notices(self):
        notices = []
        while self.has_notices():
            notices.append(self.get_notice())
        return notices

    def get_all_eose(self):
        eose = []
        while self.has_eose_notices():
            eose.append(self.get_eose_notice())
        return eose

    def get_all_ok(self):
        ok = []
        while self.has_ok_notices():
            ok.append(self.get_ok_notice())
        return ok

    def get_all(self):
        results = {"events": [], "notices": [], "eose": [], "ok": []}
        results["events"] = self.get_all_events()
        results["notices"] = self.get_all_notices()
        results["eose"] = self.get_all_eose()
        results["ok"] = self.get_all_ok()
        return results

    def get_event(self):
        return self.events.get()

    def get_notice(self):
        return self.notices.get()

    def get_eose_notice(self):
        return self.eose_notices.get()

    def get_ok_notice(self):
        return self.ok_notices.get()

    def has_events(self):
        return self.events.qsize() > 0

    def has_notices(self):
        return self.notices.qsize() > 0

    def has_eose_notices(self):
        return self.eose_notices.qsize() > 0

    def has_ok_notices(self):
        return self.ok_notices.qsize() > 0

    def _process_message(self, message: str, url: str):
        message_json = json.loads(message)
        message_type = message_json[0]
        if message_type == RelayMessageType.EVENT:
            subscription_id = message_json[1]
            e = message_json[2]
            event = Event.from_dict(e)
            with self.lock:
                if self.first_response_only:
                    object_id = event.id
                else:
                    object_id = f'{event.id}:{url}'
                if object_id not in self._unique_objects:
                    self.events.put(EventMessage(event, subscription_id, url))
                    self._unique_objects.add(event.id)
        elif message_type == RelayMessageType.NOTICE:
            self.notices.put(NoticeMessage(message_json[1], url))
        elif message_type == RelayMessageType.END_OF_STORED_EVENTS:
            self.eose_notices.put(EndOfStoredEventsMessage(message_json[1], url))
        elif message_type == RelayMessageType.OK:
            self.ok_notices.put(
                OKMessage(message_json[1], message_json[2], message_json[3], url)
            )

    def __repr__(self):
        return (
            f'Pool(events({self.events.qsize()}) notices({self.notices.qsize()}) '
            f'eose({self.eose_notices.qsize()}) ok({self.ok_notices.qsize()}))'
        )


@dataclass
class EventMessageStore:
    eventMessages: Optional[List[EventMessage]] = None

    def __post_init__(self):
        if self.eventMessages is None:
            self.eventMessages = []

    def __len__(self):
        return len(self.eventMessages)

    def __getitem__(self, key):
        return self.eventMessages[key]

    def __setitem__(self, key, value):
        self.eventMessages[key] = value

    def __iter__(self):
        return self.eventMessages.__iter__()

    def __contains__(self, item):
        return item in self.eventMessages

    def add_event(self, event):
        if isinstance(event, list):
            self.eventMessages += event
        else:
            self.eventMessages.append(event)

    def get_newest_event(self, url=None):
        if not self.eventMessages:
            return None
        if url is None:
            return max(self.eventMessages, key=lambda x: x.event.date_time())
        else:
            timestamp0 = datetime.datetime.fromtimestamp(0)
            return max(
                self.eventMessages,
                key=lambda x: x.event.date_time() if x.url == url else timestamp0,
            )

    def get_oldest_event(self, url=None):
        if not self.eventMessages:
            return None
        if url is None:
            return min(self.eventMessages, key=lambda x: x.event.date_time())
        else:
            now = datetime.datetime.now()
            return min(
                self.eventMessages,
                key=lambda x: x.event.date_time() if x.url == url else now,
            )

    def get_events_by_url(self, url):
        return [event for event in self.eventMessages if event.url == url]

    def get_events_by_id(self, subscription_id):
        return [
            event
            for event in self.eventMessages
            if event.subscription_id == subscription_id
        ]

    def __repr__(self):
        if not self.eventMessages:
            return 'EventMessageStore()'
        return f'EventMessageStore({len(self.eventMessages)} events)'
