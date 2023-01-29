from . import bech32_util


def bech32_decode(bech32_str: str):
    """Loads bytes from its bech32/nsec form."""
    hrp, data, spec = bech32_util.bech32_decode(bech32_str)
    raw_secret = bech32_util.convertbits(data, 5, 8)[:-1]
    return bytes(raw_secret)


def bech32_encode(raw_bytes: bytes, prefix: str) -> str:
    converted_bits = bech32_util.convertbits(raw_bytes, 8, 5)
    return bech32_util.bech32_encode(
        prefix, converted_bits, bech32_util.Encoding.BECH32
    )
