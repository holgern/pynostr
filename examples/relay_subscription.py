#!/usr/bin/env python

import uuid

import tornado.ioloop
from rich.console import Console
from rich.table import Table
from tornado import gen

from pynostr.base_relay import RelayPolicy
from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.key import PublicKey
from pynostr.message_pool import MessagePool
from pynostr.relay import Relay
from pynostr.utils import extract_nip05

if __name__ == "__main__":

    console = Console()

    nip05 = extract_nip05("jack@cash.app")

    author = PublicKey.from_hex(nip05[0])
    filters = FiltersList(
        [Filters(authors=[author.hex()], kinds=[EventKind.TEXT_NOTE], limit=100)]
    )

    subscription_id = uuid.uuid1().hex
    io_loop = tornado.ioloop.IOLoop.current()
    message_pool = MessagePool(first_response_only=False)
    policy = RelayPolicy()
    r = Relay("wss://relay.damus.io", message_pool, io_loop, policy)

    r.add_subscription(subscription_id, filters)

    try:
        io_loop.run_sync(r.connect)
    except gen.Return:
        pass
    io_loop.stop()

    event_msgs = message_pool.get_all_events()
    print(f"{r.url} returned {len(event_msgs)} TEXT_NOTEs from jack.")

    table = Table("date", "content")
    for event_msg in event_msgs[::-1]:
        table.add_row(str(event_msg.event.date_time()), event_msg.event.content)
    console.print(table)
