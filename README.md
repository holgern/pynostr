# pynostr
[![codecov](https://codecov.io/gh/holgern/pynostr/branch/main/graph/badge.svg?token=jIyk1cnhIx)](https://codecov.io/gh/holgern/pynostr)

Python library for for [Nostr](https://github.com/nostr-protocol/nostr).

This library is using coincurve instead of secp256k1, so pynostr can be used on windows.

## Installation
```bash
pip install pynostr
```
The necessary coincurve can be installed on android inside termux:
```bash
pkg update
pkg install build-essential
pkg-install binutils
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
