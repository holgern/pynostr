import logging
import uuid

from rich.console import Console
from tornado import gen

from pynostr.event import Event, EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.message_type import RelayMessageType
from pynostr.relay_list import RelayList
from pynostr.relay_manager import RelayManager
from pynostr.utils import get_relay_list, get_timestamp

log = logging.getLogger(__name__)


@gen.coroutine
def print_message(message_json, url):
    message_type = message_json[0]
    if message_type == RelayMessageType.EVENT:
        event = Event.from_dict(message_json[2])
        print(f"{url}: {str(event.content)}")


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
    relay_manager.add_relay_list(
        relay_list,
        timeout=0,
        close_on_eose=False,
        message_callback=print_message,
        message_callback_url=True,
    )

    filters = FiltersList([Filters(kinds=[EventKind.TEXT_NOTE], since=get_timestamp())])
    subscription_id = uuid.uuid1().hex

    relay_manager.add_subscription_on_all_relays(subscription_id, filters)

    relay_manager.run_sync()
