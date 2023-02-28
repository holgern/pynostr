import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .event import Event, EventKind
from .exception import NIPValidationException

log = logging.getLogger(__name__)


class ReportType(str, Enum):
    NUDITY = 'nudity'
    PROFANITY = 'profanity'
    ILLEGAL = 'illegal'
    SPAM = 'spam'
    IMPERSONATION = 'impersonation'


@dataclass
class Report:
    """NIP-56 reporting event."""

    content: Optional[str] = None
    pubkey: Optional[str] = None
    reported_pubkey: Optional[str] = None
    note_id: Optional[str] = None
    report_type: Optional[ReportType] = None
    victim_pubkey: Optional[str] = None

    def to_event(self) -> Event:
        if self.reported_pubkey is None:
            raise NIPValidationException(
                "Reports require the pubkey of the user being reported"
            )
        if self.report_type is None or not isinstance(self.report_type, ReportType):
            raise NIPValidationException("Reports require a valid report type")
        e = Event(content=self.content, pubkey=self.pubkey, kind=EventKind.REPORT)
        if self.note_id:
            e.tags.append(["e", self.note_id, self.report_type])
            e.tags.append(["p", self.reported_pubkey])
        else:
            e.tags.append(["p", self.reported_pubkey, self.report_type])
            if self.victim_pubkey:
                e.tags.append(["p", self.victim_pubkey])
        e.compute_id()
        return e
