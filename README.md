# pynostr

| | |
| --- | --- |
| CI/CD | [![codecov](https://codecov.io/gh/holgern/pynostr/branch/main/graph/badge.svg?token=jIyk1cnhIx)](https://codecov.io/gh/holgern/pynostr) [![CircleCI](https://dl.circleci.com/status-badge/img/gh/holgern/pynostr/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/holgern/pynostr/tree/main) |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/pynostr.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/pynostr/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pynostr.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypi.org/project/pynostr/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pynostr.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/pynostr/) |

-----

Python library for for [Nostr](https://github.com/nostr-protocol/nostr).

This library is using coincurve instead of secp256k1, so pynostr can be used on windows and is a fork from [python-nostr](https://github.com/jeffthibault/python-nostr).

This library works with python >= 3.7

## Installation
```bash
pip install pynostr
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

relay_manager = RelayManager()
relay_manager.add_relay("wss://nostr-pub.wellorder.net")
relay_manager.add_relay("wss://relay.damus.io")
filters = FiltersList([Filters(kinds=[EventKind.TEXT_NOTE], limit=100)])
subscription_id = uuid.uuid1().hex
relay_manager.add_subscription_on_all_relays(subscription_id, filters)
time.sleep(1.25)
while relay_manager.message_pool.has_notices():
    notice_msg = relay_manager.message_pool.get_notice()
    print(notice_msg.content)
while relay_manager.message_pool.has_events():
    event_msg = relay_manager.message_pool.get_event()
    print(event_msg.event.content)
relay_manager.close_all_relay_connections()
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

relay_manager = RelayManager()
relay_manager.add_relay("wss://nostr-pub.wellorder.net")
relay_manager.add_relay("wss://relay.damus.io")
time.sleep(1.25) # allow the connections to open

private_key = PrivateKey()

filters = FiltersList([Filters(authors=[private_key.public_key.hex()], limit=100)])
subscription_id = uuid.uuid1().hex
relay_manager.add_subscription_on_all_relays(subscription_id, filters)
event = Event("Hello Nostr")
event.sign(private_key.hex())

relay_manager.publish_event(event)
time.sleep(1) # allow the messages to send
while relay_manager.message_pool.has_events():
    event_msg = relay_manager.message_pool.get_event()
    print(event_msg.event.to_dict())
relay_manager.close_all_relay_connections()
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
from pynostr.event import Event, EventKind
dm = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
dm.encrypt_dm(private_key.hex()
  recipient_pubkey=recipient_pubkey,
  cleartext_content="Secret message!"
)
dm.sign(private_key.hex())
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
