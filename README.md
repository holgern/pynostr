# pynostr

| | |
| --- | --- |
| CI/CD | [![codecov](https://codecov.io/gh/holgern/pynostr/branch/main/graph/badge.svg?token=jIyk1cnhIx)](https://codecov.io/gh/holgern/pynostr) [![CircleCI](https://dl.circleci.com/status-badge/img/gh/holgern/pynostr/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/holgern/pynostr/tree/main) |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/pynostr.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/pynostr/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pynostr.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypi.org/project/pynostr/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pynostr.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/pynostr/) |

-----

Python library for for [Nostr](https://github.com/nostr-protocol/nostr).

This library is using coincurve instead of secp256k1, so pynostr can be used on windows. pynostr started as a fork from [python-nostr](https://github.com/jeffthibault/python-nostr)
and is now developed on its own.

This library works with python >= 3.7

## Features

[NIPs](https://github.com/nostr-protocol/nips) with a relay-specific implementation are listed here.

- [x] NIP-01: Basic protocol flow description
- [x] NIP-02: Contact List and Petnames
- [x] NIP-03: OpenTimestamps Attestations for Events
- [x] NIP-04: Encrypted Direct Message
- [x] NIP-05: Mapping Nostr keys to DNS-based internet identifiers
- [ ] NIP-06: Basic key derivation from mnemonic seed phrase
- [ ] NIP-08: Handling Mentions
- [ ] NIP-09: Event Deletion
- [x] NIP-10: Conventions for clients' use of e and p tags in text events
- [x] NIP-11: Relay Information Document
- [ ] NIP-12: Generic Tag Queries
- [x] NIP-13: Proof of Work
- [ ] NIP-14: Subject tag in text events.
- [x] NIP-15: End of Stored Events Notice
- [ ] NIP-16: Event Treatment
- [x] NIP-19: bech32-encoded entities
- [ ] NIP-20: Command Results
- [ ] NIP-21: nostr: URL scheme
- [ ] NIP-22: Event created_at Limits
- [ ] NIP-23: Long-form Content
- [ ] NIP-25: Reactions
- [x] NIP-26: Delegated Event Signing
- [ ] NIP-28: Public Chat
- [ ] NIP-33: Parameterized Replaceable Events
- [ ] NIP-36: Sensitive Content
- [ ] NIP-40: Expiration Timestamp
- [ ] NIP-42: Authentication of clients to relays
- [ ] NIP-46: Nostr Connect
- [ ] NIP-50: Keywords filter
- [x] NIP-56: Reporting
- [ ] NIP-57: Lightning Zaps
- [ ] NIP-58: Badges
- [x] NIP-65: Relay List Metadata

## Differences from python-nostr

* tornado websockets
* coincurve secp256k1 implementation
* no proxies
* no ssl_options
* relay can be used to open a connection to a relay

| python-nostr | pynostr |
| --- | --- |
| Filter | Filters |
| Filters | FiltersList |
| relay_manager.open_connections | relay_manager.run_sync() |
| relay_manager.close_connections() | - |
| private_key.sign_event(event) | event.sign(private_key.hex()) |



## Installation
```bash
pip install pynostr
```
with websocket-client support
```bash
pip install pynostr[websocket-client]
```
The necessary coincurve can be installed on android inside termux:
```bash
pkg update
pkg install build-essential
pkg install binutils
pkg install python-cryptography
pip install coincurve --no-binary all
```

## Usage
**Generate a key**
```python
from pynostr.key import PrivateKey

private_key = PrivateKey()
public_key = private_key.public_key
print(f"Private key: {private_key.bech32()}")
print(f"Public key: {public_key.bech32()}")
```

**Connect to relays**
```python
from pynostr.relay_manager import RelayManager
from pynostr.filters import FiltersList, Filters
from pynostr.event import EventKind
import time
import uuid

relay_manager = RelayManager(timeout=2)
relay_manager.add_relay("wss://nostr-pub.wellorder.net")
relay_manager.add_relay("wss://relay.damus.io")
filters = FiltersList([Filters(kinds=[EventKind.TEXT_NOTE], limit=100)])
subscription_id = uuid.uuid1().hex
relay_manager.add_subscription_on_all_relays(subscription_id, filters)
relay_manager.run_sync()
while relay_manager.message_pool.has_notices():
    notice_msg = relay_manager.message_pool.get_notice()
    print(notice_msg.content)
while relay_manager.message_pool.has_events():
    event_msg = relay_manager.message_pool.get_event()
    print(event_msg.event.content)
relay_manager.close_all_relay_connections()
```

**Connect to single relay**
```python
from pynostr.relay import Relay
from pynostr.filters import FiltersList, Filters
from pynostr.event import EventKind
from pynostr.base_relay import RelayPolicy
from pynostr.message_pool import MessagePool
import tornado.ioloop
from tornado import gen
import time
import uuid

message_pool = MessagePool(first_response_only=False)
policy = RelayPolicy()
io_loop = tornado.ioloop.IOLoop.current()
r = Relay(
    "wss://relay.damus.io",
    message_pool,
    io_loop,
    policy,
    timeout=2
)
filters = FiltersList([Filters(kinds=[EventKind.TEXT_NOTE], limit=100)])
subscription_id = uuid.uuid1().hex

r.add_subscription(subscription_id, filters)

try:
    io_loop.run_sync(r.connect)
except gen.Return:
    pass
io_loop.stop()

while message_pool.has_notices():
    notice_msg = message_pool.get_notice()
    print(notice_msg.content)
while message_pool.has_events():
    event_msg = message_pool.get_event()
    print(event_msg.event.content)
```


**Publish to relays**
```python
import json
import ssl
import time
import uuid
from pynostr.event import Event
from pynostr.relay_manager import RelayManager
from pynostr.filters import FiltersList, Filters
from pynostr.message_type import ClientMessageType
from pynostr.key import PrivateKey

relay_manager = RelayManager(timeout=6)
relay_manager.add_relay("wss://nostr-pub.wellorder.net")
relay_manager.add_relay("wss://relay.damus.io")
private_key = PrivateKey()

filters = FiltersList([Filters(authors=[private_key.public_key.hex()], limit=100)])
subscription_id = uuid.uuid1().hex
relay_manager.add_subscription_on_all_relays(subscription_id, filters)

event = Event("Hello Nostr")
event.sign(private_key.hex())

relay_manager.publish_event(event)
relay_manager.run_sync()
time.sleep(5) # allow the messages to send
while relay_manager.message_pool.has_ok_notices():
    ok_msg = relay_manager.message_pool.get_ok_notice()
    print(ok_msg)
while relay_manager.message_pool.has_events():
    event_msg = relay_manager.message_pool.get_event()
    print(event_msg.event.to_dict())

```

**Reply to a note**
```python
from pynostr.event import Event
reply = Event(
  content="Sounds good!",
)
# create 'e' tag reference to the note you're replying to
reply.add_event_ref(original_note_id)
# create 'p' tag reference to the pubkey you're replying to
reply.add_pubkey_ref(original_note_author_pubkey)
reply.sign(private_key.hex())
```

**Send a DM**
```python
from pynostr.encrypted_dm import EncryptedDirectMessage
from pynostr.key import PrivateKey
private_key = PrivateKey()
recipient_pubkey = PrivateKey().public_key.hex()
dm = EncryptedDirectMessage()
dm.encrypt(private_key.hex(),
  recipient_pubkey=recipient_pubkey,
  cleartext_content="Secret message!"
)
dm_event = dm.to_event()
dm_event.sign(private_key.hex())
```

**NIP-26 delegation**
```python
from pynostr.delegation import Delegation
from pynostr.event import EventKind, Event
from pynostr.key import PrivateKey

# Load your "identity" PK that you'd like to keep safely offline
identity_pk = PrivateKey.from_nsec("nsec1...")

# Create a new, disposable PK as the "delegatee" that can be "hot" in a Nostr client
delegatee_pk = PrivateKey()

# the "identity" PK will authorize "delegatee" to sign TEXT_NOTEs on its behalf for the next month
delegation = Delegation(
    delegator_pubkey=identity_pk.public_key.hex(),
    delegatee_pubkey=delegatee_pk.public_key.hex(),
    event_kind=EventKind.TEXT_NOTE,
    duration_secs=30*24*60*60
)

identity_pk.sign_delegation(delegation)

event = Event(
    "Hello, NIP-26!",
    tags=[delegation.get_tag()],
)
event.sign(self.delegatee_pk.hex())

# ...normal broadcast steps...
```
**NIP-13: Proof of Work**
```python
from pynostr.event import Event
from pynostr.pow import PowEvent
pe = PowEvent(difficulty=25)
e=Event()
e=pe.mine(e)
assert pe.check_difficulty(e)
```

## Test Suite

### Set up the test environment

Install the test-runner dependencies:
```
pip3 install -r test-requirements.txt
```

Then make the `pynostr` python module visible/importable to the tests by installing the local dev dir as an editable module:
```
# from the repo root
pip3 install -e .
```

### Running the test suite
Run the whole test suite:
```
# from the repo root
pytest
```

Run a specific test file:
```
pytest test/test_this_file.py
```

Run a specific test:
```
pytest test/test_this_file.py::test_this_specific_test
```

### Running tests with tox

Install tox

```
pip install tox
```

Run tests

```
tox
```

## Pre-commit-config

### Installation

```
$ pip install pre-commit
```

### Using homebrew:
```
$ brew install pre-commit
```

```
$ pre-commit --version
pre-commit 2.10.0
```

### Install the git hook scripts

```
$ pre-commit install
```

### Run against all the files
```
pre-commit run --all-files
pre-commit run --show-diff-on-failure --color=always --all-files
```

### Update package rev in pre-commit yaml
```bash
pre-commit autoupdate
pre-commit run --show-diff-on-failure --color=always --all-files
```
