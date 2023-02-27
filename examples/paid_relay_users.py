import concurrent.futures
import datetime
import logging
import uuid

from rich.console import Console
from rich.table import Table

from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.message_pool import EventMessageStore
from pynostr.relay_manager import RelayManager
from pynostr.utils import get_relay_information, get_relay_list, get_timestamp

log = logging.getLogger(__name__)

if __name__ == "__main__":

    console = Console()
    MAX_THREADS = 16

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch = logging.StreamHandler()
    ch.setLevel(4)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    relay_list = get_relay_list()

    paid_relays = {}
    print(f"Checking {len(relay_list)} relays...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        res = executor.map(get_relay_information, relay_list)
        for relay_info in res:
            if relay_info is not None and "limitation" in relay_info:
                if "payment_required" in relay_info["limitation"]:
                    if relay_info["limitation"]["payment_required"]:
                        if (
                            "fees" not in relay_info
                            or len(relay_info["fees"]['admission']) == 0
                        ):
                            paid_relays[relay_info["url"]] = 0
                        elif "amount" in relay_info["fees"]['admission'][0]:
                            paid_relays[relay_info["url"]] = (
                                relay_info["fees"]['admission'][0]['amount'] / 1000
                            )
    print(f"Found {len(paid_relays)} relays with fee!")
    relay_manager = RelayManager(error_threshold=10, timeout=5)
    for url in paid_relays.keys():
        relay_manager.add_relay(url)

    events = EventMessageStore()
    events_by_relay = {}
    unix_timestamp = get_timestamp(days=7)
    now = datetime.datetime.utcnow()

    filters = FiltersList(
        [Filters(kinds=[EventKind.TEXT_NOTE], since=unix_timestamp, limit=500)]
    )
    subscription_id = uuid.uuid1().hex
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    relay_manager.run_sync()

    event_messages = relay_manager.message_pool.get_all_events()
    events.add_event(event_messages)

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
