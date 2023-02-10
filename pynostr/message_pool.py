"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import json
from dataclasses import dataclass
from queue import Queue
from threading import Lock

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
        self._unique_objects: set = set()
        self.lock: Lock = Lock()

    def add_message(self, message: str, url: str):
        self._process_message(message, url)

    def get_all(self):
        results = {"events": [], "notices": [], "eose": []}
        while self.has_events():
            results["events"].append(self.get_event())
        while self.has_notices():
            results["notices"].append(self.get_notice())
        while self.has_eose_notices():
            results["eose"].append(self.get_eose_notice())
        return results

    def get_event(self):
        return self.events.get()

    def get_notice(self):
        return self.notices.get()

    def get_eose_notice(self):
        return self.eose_notices.get()

    def has_events(self):
        return self.events.qsize() > 0

    def has_notices(self):
        return self.notices.qsize() > 0

    def has_eose_notices(self):
        return self.eose_notices.qsize() > 0

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

    def __repr__(self):
        return (
            f'Pool(events({self.events.qsize()}) notices({self.notices.qsize()}) '
            f'eose({self.eose_notices.qsize()}))'
        )
