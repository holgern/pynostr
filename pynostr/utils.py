import binascii
import logging

import requests
import tlv8

from . import bech32

log = logging.getLogger(__name__)


def bech32_decode(bech32_str: str):
    """Loads bytes from its bech32/nsec form."""
    hrp, data, spec = bech32.bech32_decode(bech32_str)
    raw_secret = bech32.convertbits(data, 5, 8)[:-1]
    return bytes(raw_secret)


def bech32_encode(raw_bytes: bytes, prefix: str) -> str:
    converted_bits = bech32.convertbits(raw_bytes, 8, 5)
    return bech32.bech32_encode(prefix, converted_bits, bech32.Encoding.BECH32)


def split_nip05(nip05):
    if nip05 is None:
        return None, None
    if "@" in nip05:
        name, url = nip05.lower().split("@")
    else:
        name = "_"
        url = nip05.lower()
    return name, url


def get_nip05_response(name, url):
    if url is None:
        return {}
    request_url = f"https://{url}/.well-known/nostr.json?name={name}"
    try:
        response = requests.get(request_url, timeout=5)

        response.raise_for_status()

        return response.json()
    except requests.exceptions.Timeout:
        # Handle a timeout error
        log.warning("Request timed out. Please try again later.")

    except requests.exceptions.HTTPError as err:
        # Handle an HTTP error
        log.warning(f"HTTP error occurred: {err}")

    except requests.exceptions.RequestException as err:
        # Handle any other request exception
        log.warning(f"An error occurred: {err}")
    return None


def check_nip05(nip05_response: dict, name: str):
    if len(nip05_response) == 0:
        return
    if "names" in nip05_response:
        if name in nip05_response["names"]:
            pubkey = nip05_response["names"][name]
        else:
            pubkey = None
    else:
        pubkey = None
    if "relays" in nip05_response and pubkey is not None:
        if pubkey in nip05_response["relays"]:
            relays = nip05_response["relays"][pubkey]
        else:
            relays = None
    else:
        relays = None
    return pubkey, relays


def extract_nip05(nip05: str):
    name, url = split_nip05(nip05)
    nip05_response = get_nip05_response(name, url)
    return check_nip05(nip05_response, name)


def get_relay_information(url: str):
    headers = {'Accept': 'application/nostr+json'}
    if "wss" in url:
        metadata_uri = url.replace("wss", "https")
    elif "ws" in url:
        metadata_uri = url.replace("ws", "http")
    else:
        raise Exception(f"{url} is not a websocket url")
    try:
        response = requests.get(metadata_uri, headers=headers, timeout=5)

        response.raise_for_status()

        metadata = response.json()
        return metadata
    except requests.exceptions.Timeout:
        # Handle a timeout error
        log.warning("Request timed out. Please try again later.")

    except requests.exceptions.HTTPError as err:
        # Handle an HTTP error
        log.warning(f"HTTP error occurred: {err}")

    except requests.exceptions.RequestException as err:
        # Handle any other request exception
        log.warning(f"An error occurred: {err}")


def nprofile_decode(nprofile: str):
    decode = bytes(bech32_decode(nprofile))
    pubkey = None
    relays = []
    for data in tlv8.deep_decode(decode):
        if data.type_id == 0:
            pubkey = binascii.hexlify(data.data).decode()
        elif data.type_id == 1:
            relays.append(data.data.decode())
    return pubkey, relays


def nprofile_encode(pubkey: str, relays: [str]):
    structure = [
        tlv8.Entry(0, binascii.unhexlify(pubkey)),
    ]
    for relay in relays:
        structure.append(tlv8.Entry(1, relay.encode()))

    bytes_data = tlv8.encode(structure)

    bytes_data = b''
    for entry in structure:
        bytes_data += entry.encode()
    return bech32_encode(bytes_data, "nprofile")