import base64
import binascii
import secrets
from hashlib import sha256
from typing import Optional

import coincurve as secp256k1
from coincurve._libsecp256k1 import ffi, lib
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .delegation import Delegation
from .utils import bech32_decode, bech32_encode

HAS_ECDH = hasattr(lib, 'secp256k1_ecdh')


class PublicKey:
    def __init__(self, raw_bytes: bytes) -> None:
        """
        :param raw_bytes: The formatted public key.
        :type data: bytes
        """
        if isinstance(raw_bytes, PrivateKey):
            self.raw_bytes = raw_bytes.public_key.raw_bytes
        elif isinstance(raw_bytes, secp256k1.keys.PublicKey):
            self.raw_bytes = raw_bytes.format(compressed=True)[2:]
        elif isinstance(raw_bytes, secp256k1.keys.PublicKeyXOnly):
            self.raw_bytes = raw_bytes.format()
        elif isinstance(raw_bytes, str):
            self.raw_bytes = binascii.unhexlify(raw_bytes)
        else:
            self.raw_bytes = raw_bytes

    def bech32(self) -> str:
        return bech32_encode(self.raw_bytes, "npub")

    @property
    def npub(self):
        return self.bech32()

    def hex(self) -> str:
        return self.raw_bytes.hex()

    def verify(self, sig: bytes, message: bytes) -> bool:
        pk = secp256k1.PublicKeyXOnly(self.raw_bytes)
        return pk.verify(sig, message)

    @classmethod
    def from_hex(cls, hex: str) -> 'PublicKey':
        return cls(bytes.fromhex(hex))

    @classmethod
    def from_npub(cls, npub: str):
        """Load a PublicKey from its bech32/npub form."""
        return cls(bytes(bech32_decode(npub)))

    def __repr__(self):
        pubkey = self.bech32()
        return f'PublicKey({pubkey[:10]}...{pubkey[-10:]})'

    def __eq__(self, other):
        return isinstance(other, PublicKey) and self.raw_bytes == other.raw_bytes

    def __hash__(self):
        return hash(self.raw_bytes)

    def __str__(self):
        """Return public key in hex form
        :return: string
        :rtype: str
        """
        return self.hex()

    def __bytes__(self):
        """Return raw bytes
        :return: Raw bytes
        :rtype: bytes
        """
        return self.raw_bytes


class PrivateKey:
    def __init__(self, raw_secret: Optional[bytes] = None) -> None:
        """
        :param raw_secret: The secret used to initialize the private key.
                           If not provided or `None`, a new key will be generated.
        :type raw_secret: bytes
        """
        if raw_secret is not None:
            self.raw_secret = raw_secret
        else:
            self.raw_secret = secrets.token_bytes(32)

        sk = secp256k1.PrivateKey(self.raw_secret)
        self.public_key = PublicKey(sk.public_key_xonly)

    @classmethod
    def from_nsec(cls, nsec: str):
        """Load a PrivateKey from its bech32/nsec form.

        :param nsec: the nsec key to be imported
        """
        return cls(bytes(bech32_decode(nsec)))

    @classmethod
    def from_hex(cls, hex: str):
        """Load a PrivateKey from its hex form."""
        return cls(binascii.unhexlify(hex))

    def bech32(self) -> str:
        return bech32_encode(self.raw_secret, "nsec")

    @property
    def nsec(self):
        return self.bech32()

    def __hash__(self):
        return hash(self.raw_secret)

    def __eq__(self, other):
        return isinstance(other, PrivateKey) and self.raw_secret == other.raw_secret

    def hex(self) -> str:
        return self.raw_secret.hex()

    def ecdh(self, public_key_hex):
        assert public_key_hex, "No public key defined"
        if not HAS_ECDH:
            raise Exception("secp256k1_ecdh not enabled")
        sk = secp256k1.PrivateKey(self.raw_secret)
        result = ffi.new('char [32]')
        pk = secp256k1.PublicKey(bytes.fromhex("02" + public_key_hex))
        res = lib.secp256k1_ecdh(
            sk.context.ctx, result, pk.public_key, self.raw_secret, copy_x, ffi.NULL
        )
        if not res:
            raise Exception(f'invalid scalar ({res})')

        return bytes(ffi.buffer(result, 32))

    def tweak_add(self, scalar: bytes) -> bytes:
        sk = secp256k1.PrivateKey(self.raw_secret)
        return sk.add(scalar)

    def compute_shared_secret(self, public_key_hex: str) -> bytes:
        return self.ecdh(public_key_hex)

    def encrypt_message(self, message: str, public_key_hex: str) -> str:
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()

        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(self.compute_shared_secret(public_key_hex)), modes.CBC(iv)
        )

        encryptor = cipher.encryptor()
        encrypted_message = encryptor.update(padded_data) + encryptor.finalize()

        ret_part1 = base64.b64encode(encrypted_message).decode()
        ret_part2 = base64.b64encode(iv).decode()
        return f"{ret_part1}?iv={ret_part2}"

    def decrypt_message(self, encoded_message: str, public_key_hex: str) -> str:
        encoded_data = encoded_message.split('?iv=')
        encoded_content, encoded_iv = encoded_data[0], encoded_data[1]

        iv = base64.b64decode(encoded_iv)
        cipher = Cipher(
            algorithms.AES(self.compute_shared_secret(public_key_hex)), modes.CBC(iv)
        )
        encrypted_content = base64.b64decode(encoded_content)

        decryptor = cipher.decryptor()
        decrypted_message = decryptor.update(encrypted_content) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_message) + unpadder.finalize()

        return unpadded_data.decode()

    def sign(self, message: bytes, aux_randomness: bytes = b'') -> str:
        sk = secp256k1.PrivateKey(self.raw_secret)
        return sk.sign_schnorr(message, aux_randomness)

    def sign_delegation(self, delegation: Delegation) -> None:
        delegation.signature = self.sign(
            sha256(delegation.delegation_token.encode()).digest()
        ).hex()

    def __repr__(self):
        pubkey = self.public_key.bech32()
        return f'PrivateKey({pubkey[:10]}...{pubkey[-10:]})'

    def __str__(self):
        """Return private key in hex form
        :return: hex string
        :rtype: str
        """
        return self.hex()

    def __bytes__(self):
        """Return raw bytes
        :return: Raw bytes
        :rtype: bytes
        """
        return self.raw_secret


@ffi.callback(
    "int (unsigned char *, const unsigned char *, const unsigned char *, void *)"
)
def copy_x(output, x32, y32, data):
    ffi.memmove(output, x32, 32)
    return 1
