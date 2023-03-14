import logging
import uuid

from rich.console import Console
from tornado import gen

from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.message_type import RelayMessageType
from pynostr.relay_list import RelayList
from pynostr.relay_manager import RelayManager
from pynostr.utils import get_public_key, get_relay_list, get_timestamp

log = logging.getLogger(__name__)


@gen.coroutine
def print_message(message_json):
    message_type = message_json[0]
    if message_type == RelayMessageType.EVENT:
        print("1: " + str(message_json))


if __name__ == "__main__":

    console = Console()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch = logging.StreamHandler()
    ch.setLevel(4)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    identity_str = input("Get following for identity (npub or nip05): ")
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

    print(f"Found {len(relay_list.data)} relays...")

    # timeout must set to 0 and close_on_eose must set to False
    relay_manager = RelayManager(error_threshold=3, timeout=0)
    relay_manager.add_relay_list(
        relay_list, close_on_eose=False, message_callback=print_message
    )

    start_time = get_timestamp()

    filters = FiltersList(
        [  # enter filter condition
            Filters(
                since=start_time,
                kinds=[EventKind.TEXT_NOTE],
                pubkey_refs=[
                    identity.hex(),
                ],
            )
        ]
    )
    subscription_id = uuid.uuid1().hex
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)
    relay_manager.run_sync()
