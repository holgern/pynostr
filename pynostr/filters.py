"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import json
from collections import UserList
from dataclasses import dataclass
from typing import List, Optional

from .event import Event, EventKind


@dataclass
class Filters:
    """NIP-01 filtering. Explicitly supports "#e" and "#p" tag filters via `event_refs`
    and `pubkey_refs`. Arbitrary NIP-12 single-letter tag filters are also supported via
    `add_arbitrary_tag`. If a particular single-letter tag gains prominence, explicit
    support should be added. For example:

    # arbitrary tag
    filter.add_arbitrary_tag('t', [hashtags])

    # promoted to explicit support
    Filters(hashtag_refs=[hashtags])
    """

    ids: Optional[List[str]] = None
    kinds: Optional[List[EventKind]] = None
    authors: Optional[List[str]] = None
    since: Optional[int] = None
    until: Optional[int] = None
    event_refs: Optional[
        List[str]
    ] = None  # the "#e" attr; list of event ids referenced in an "e" tag
    pubkey_refs: Optional[
        List[str]
    ] = None  # The "#p" attr; list of pubkeys referenced in a "p" tag
    limit: Optional[int] = None

    def __post_init__(self):
        self.tags = {}
        if self.event_refs:
            self.add_arbitrary_tag('e', self.event_refs)
        if self.pubkey_refs:
            self.add_arbitrary_tag('p', self.pubkey_refs)

    def add_arbitrary_tag(self, tag: str, values: list):
        """Filter on any arbitrary tag with explicit handling for NIP-01 and NIP-12
        single-letter tags."""
        # NIP-01 'e' and 'p' tags and any NIP-12 single-letter tags must be
        # prefixed with "#"
        tag_key = tag if len(tag) > 1 else f"#{tag}"
        self.tags[tag_key] = values

    @classmethod
    def from_json(cls, filters):
        if "ids" in filters:
            ret = cls(filters["ids"])
        else:
            ret = cls("")
        if "authors" in filters:
            ret.authors = filters["authors"]
        if "kinds" in filters:
            ret.kinds = filters["kinds"]
        if "#e" in filters:
            ret.event_refs = filters["#e"]
        if "#p" in filters:
            ret.pubkey_refs = filters["#p"]
        if "since" in filters:
            ret.since = filters["since"]
        if "until" in filters:
            ret.until = filters["until"]
        if "limit" in filters:
            ret.limit = filters["limit"]
        cls.tags = {}
        if cls.event_refs:
            cls.add_arbitrary_tag('e', cls.event_refs)
        if cls.pubkey_refs:
            cls.add_arbitrary_tag('p', cls.pubkey_refs)
        return ret

    def matches(self, event: Event) -> bool:
        if self.ids is not None and event.id not in self.ids:
            return False
        if self.kinds is not None and event.kind not in self.kinds:
            return False
        if self.authors is not None and event.pubkey not in self.authors:
            return False
        if self.since is not None and event.created_at < self.since:
            return False
        if self.until is not None and event.created_at > self.until:
            return False
        if (self.event_refs is not None or self.pubkey_refs is not None) and len(
            event.tags
        ) == 0:
            return False

        if self.tags:
            e_tag_identifiers = {e_tag[0] for e_tag in event.tags}
            for f_tag, f_tag_values in self.tags.items():
                # Omit any NIP-01 or NIP-12 "#" chars on single-letter tags
                f_tag = f_tag.replace("#", "")

                if f_tag not in e_tag_identifiers:
                    # Event is missing a tag type that we're looking for
                    return False

                # Multiple values within f_tag_values are treated as OR search; an Event
                # needs to match only one.
                # Note: an Event could have multiple entries of the same tag type
                # (e.g. a reply to multiple people) so we have to check all of them.
                match_found = False
                for e_tag in event.tags:
                    if e_tag[0] == f_tag and e_tag[1] in f_tag_values:
                        match_found = True
                        break
                if not match_found:
                    return False

        return True

    def to_json_object(self) -> dict:
        res = {}
        if self.ids is not None:
            res["ids"] = self.ids
        if self.kinds is not None:
            res["kinds"] = self.kinds
        if self.authors is not None:
            res["authors"] = self.authors
        if self.since is not None:
            res["since"] = self.since
        if self.until is not None:
            res["until"] = self.until
        if self.tags is not None:
            for tag, values in self.tags.items():
                res[tag] = values
        if self.limit is not None:
            res["limit"] = self.limit
        if self.tags:
            res.update(self.tags)
        return res

    def __repr__(self):
        return f'Filters({self.to_json_object()})'

    def __str__(self):
        return json.dumps(self.to_json_object())


class FiltersList(UserList):
    def __init__(self, initlist: List[Filters] = None) -> None:
        super().__init__(initlist)
        self.data: List[Filters]

    def match(self, event: Event):
        for filters in self.data:
            if filters.matches(event):
                return True
        return False

    def to_json_array(self) -> list:
        return [filters.to_json_object() for filters in self.data]

    def __repr__(self):
        return f'FilterList({self.to_json_array()})'

    def __str__(self):
        return json.dumps(self.to_json_array())
