import click
import json
import ssl
import time
import uuid

import pynostr
from pynostr.key import PrivateKey, PublicKey


@click.group(chain=True)
def main():
    """
    Python CLI for nostr, enjoy. :)"""

@main.command()
def keygen():
    """
    creates a private and public key
    """
    private_key = PrivateKey()
    public_key = private_key.public_key
    click.echo(f"Private key: {private_key.bech32()}")
    click.echo(f"Public key: {public_key.bech32()}")


@main.command()
@click.argument('npub', type=str)
def convert(npub: str):
    """
    converts npub key to hex
    """
    public_key = PublicKey.from_npub(npub)
    click.echo(f"npub: {public_key.bech32()}")
    click.echo(f"hex: {public_key.hex()}")


@main.command()
def version():
    """shows version"""
    click.echo(pynostr.__version__)


if __name__ == "__main__":
    main()
