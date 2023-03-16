import datetime
import logging
import time
import uuid

from rich.console import Console
from rich.table import Table

from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.message_pool import EventMessageStore
from pynostr.relay_list import RelayList
from pynostr.relay_manager import RelayManager
from pynostr.utils import get_relay_list, get_timestamp

log = logging.getLogger(__name__)

if __name__ == "__main__":

    console = Console()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch = logging.StreamHandler()
    ch.setLevel(4)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    relay_list = RelayList()
    relay_list.append_url_list(get_relay_list("paid"))

    paid_relays = {}
    print(f"Checking {len(relay_list.data)} relays...")

    relay_list.update_relay_information(timeout=0.5)
    relay_list.drop_empty_metadata()

    for relay in relay_list.data:
        relay_info = relay.metadata
        if relay_info is not None and "limitation" in relay_info:
            if "payment_required" in relay_info["limitation"]:
                if relay_info["limitation"]["payment_required"]:
                    if (
                        "fees" not in relay_info
                        or len(relay_info["fees"]['admission']) == 0
                    ):
                        continue
                    elif "amount" in relay_info["fees"]['admission'][0]:
                        paid_relays[relay.url] = (
                            relay_info["fees"]['admission'][0]['amount'] / 1000
                        )
    print(f"Found {len(paid_relays)} relays with fee!")
    relay_manager = RelayManager(error_threshold=2)
    relay_manager.add_relay_list(relay_list, close_on_eose=True, timeout=5)

    events = EventMessageStore()
    events_by_relay = {}
    unix_timestamp = get_timestamp(days=1)
    now = datetime.datetime.utcnow()

    filters = FiltersList(
        [Filters(kinds=[EventKind.TEXT_NOTE], since=unix_timestamp, limit=500)]
    )
    subscription_id = uuid.uuid1().hex
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    relay_manager.run_sync()

    event_messages = relay_manager.message_pool.get_all_events()
    events.add_event(event_messages)

    # relay_manager.close_subscription_on_all_relays(subscription_id)
    oldest_event = {}
    url_list = list(relay_manager.relays.keys()).copy()
    for url in url_list:
        event_msg = events.get_newest_event(url)
        if event_msg.url != url:
            print(f"Close relay {url}")
            relay_manager.remove_relay(url)
            continue
        oldest_event[url] = event_msg.event

    relay_left = True
    count = 0
    while relay_left and count < 100:
        count += 1
        relay_manager.remove_closed_relays()
        print(f"Run {count} - {len(relay_manager.relays)} relays")
        relay_left = len(relay_manager.relays) > 0
        filters_url = {}
        subscription_id_url = {}
        url_list = list(relay_manager.relays.keys()).copy()

        for url in url_list:
            event_msg = events.get_oldest_event(url)
            if event_msg.url != url:
                print(f"Close relay {url}")
                relay_manager.remove_relay(url)
                continue
            elif oldest_event[url] == event_msg.event:
                print(f"No new events! Closing relay {url}")
                relay_manager.remove_relay(url)
                continue
            oldest_event[url] = event_msg.event
            filters_url[url] = FiltersList(
                [
                    Filters(
                        kinds=[EventKind.TEXT_NOTE],
                        since=unix_timestamp,
                        until=event_msg.event.created_at - 1,
                        limit=500,
                    )
                ]
            )
            subscription_id_url[url] = uuid.uuid1().hex
            relay_manager.add_subscription_on_relay(
                url, subscription_id_url[url], filters_url[url]
            )

        relay_manager.run_sync()
        event_messages = relay_manager.message_pool.get_all_events()
        events.add_event(event_messages)
    time.sleep(4)
    relay_manager.close_subscription_on_all_relays(subscription_id)

    while relay_manager.close_connections():
        time.sleep(1)
        relay_manager.remove_closed_relays()
        print(f"sleeping {len(relay_manager.relays)} relays still connected")

    for url in paid_relays.keys():

        event_list = events.get_events_by_url(url)
        oldest_timestamp = now
        events_by_relay[url] = {
            "pubkey": [],
            "n_pubkey": 0,
            "admission": paid_relays[url],
            "oldest_event": None,
            "n_events": len(event_list),
        }
        for e in event_list:
            if e.event.date_time() < oldest_timestamp:
                oldest_timestamp = e.event.date_time()
            if e.event.pubkey not in events_by_relay[url]["pubkey"]:
                events_by_relay[url]["pubkey"].append(e.event.pubkey)
        events_by_relay[url]["oldest_event"] = oldest_timestamp
        events_by_relay[url]["n_pubkey"] = len(events_by_relay[url]['pubkey'])

    relay_list = sorted(events_by_relay.items(), key=lambda item: item)
    relay_list2 = sorted(relay_list, key=lambda item: item[1]["n_pubkey"])

    table = Table("url", "n_pubkey", "n_events", "age oldest_event", "fee")
    for r in relay_list2[::-1]:
        table.add_row(
            r[0],
            str(r[1]['n_pubkey']),
            str(r[1]['n_events']),
            f"{(now - r[1]['oldest_event']).total_seconds() / 60 / 60} h",
            str(r[1]['admission']),
        )
    console.print(table)
