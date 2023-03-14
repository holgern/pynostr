import datetime
import logging
import uuid

from rich.console import Console
from rich.table import Table

from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.message_pool import EventMessageStore
from pynostr.metadata import Metadata
from pynostr.relay_list import RelayList
from pynostr.relay_manager import RelayManager
from pynostr.utils import get_public_key, get_relay_list, get_timestamp

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

    identity_str = input("Get metadata for identity (npub or nip05): ")
    identity = get_public_key(identity_str)

    if identity != "":
        print(f"identity is set to {identity.bech32()}")
    else:
        raise Exception("identity not valid")

    relay_list = RelayList()
    relay_list.append_url_list(get_relay_list())

    print(f"Checking {len(relay_list.data)} relays...")

    relay_list.update_relay_information(timeout=0.5)
    relay_list.drop_empty_metadata()

    print(f"Found {len(relay_list.data)} relays and start searching for metadata...")

    relay_manager = RelayManager(error_threshold=3, timeout=1)
    relay_manager.add_relay_list(relay_list)

    events = EventMessageStore()
    events_by_relay = {}
    unix_timestamp = get_timestamp(days=7)
    now = datetime.datetime.utcnow()

    filters = FiltersList(
        [Filters(authors=[identity.hex()], kinds=[EventKind.SET_METADATA], limit=1)]
    )
    subscription_id = uuid.uuid1().hex
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    relay_manager.run_sync()

    event_messages = relay_manager.message_pool.get_all_events()
    events.add_event(event_messages)

    for url in relay_list.get_url_list():

        event_list = events.get_events_by_url(url)
        if len(event_list) == 0:
            continue
        oldest_timestamp = now
        events_by_relay[url] = {"timestamp": None, "metadata": None}
        m = Metadata.from_event(event_list[0].event)
        events_by_relay[url]["timestamp"] = event_list[0].event.date_time()
        events_by_relay[url]["metadata"] = m

    relay_list = sorted(events_by_relay.items(), key=lambda item: item)
    relay_list2 = sorted(relay_list, key=lambda item: item[1]["timestamp"])

    table = Table("url", "timestamp")
    for r in relay_list2[::-1]:
        table.add_row(
            r[0],
            str(r[1]['timestamp']),
        )
    console.print(table)
    console.print(f"Metadata from {identity_str} at {relay_list2[-1][0]}")
    newest_metadata = relay_list2[-1][1]["metadata"]
    table = Table("key", "value")
    for key, value in newest_metadata.metadata_to_dict().items():
        table.add_row(key, value)
    console.print(table)

    if len(newest_metadata.identities) > 0:
        table = Table("claim_type", "identity", "proof")
        for identity in newest_metadata.identities:
            table.add_row(identity.claim_type, identity.identity, identity.proof)

        console.print(table)
