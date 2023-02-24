import logging

import click
import typer
from rich.console import Console
from rich.table import Table

from pynostr.key import PrivateKey, PublicKey
from pynostr.metadata import Metadata
from pynostr.utils import get_relay_information, nprofile_decode

log = logging.getLogger(__name__)
app = typer.Typer()
console = Console()

state = {"verbose": 3}


@app.command()
def keygen():
    """Creates a private and public key."""
    private_key = PrivateKey()
    public_key = private_key.public_key
    click.echo(f"Private key: {private_key.bech32()}")
    click.echo(f"Public key: {public_key.bech32()}")


@app.command()
def convert(identifier: str):
    """Converts npub key to hex."""
    if "npub" in identifier:
        public_key = PublicKey.from_npub(identifier)
    else:
        public_key = PublicKey.from_hex(identifier)
    click.echo(f"npub: {public_key.bech32()}")
    click.echo(f"hex: {public_key.hex()}")


@app.command()
def info(objects: str):
    """Basic info about object."""
    if "wss" in objects:
        relay_info = get_relay_information(objects)
        if relay_info is None:
            return
        table = Table("key", "value")
        for key, value in relay_info.items():
            if key in ["limitation"]:
                continue
            table.add_row(key, str(value))

        console.print(table)
        if "limitation" in relay_info:
            table = Table("key", "value")
            for key, value in relay_info["limitation"].items():
                table.add_row(key, str(value))
            console.print(table)
    elif "." in objects:
        m = Metadata.from_nip05(objects.lower())
        table = Table("key", "value")
        table.add_row("pubkey", str(m.pubkey))
        table.add_row("npub", str(PublicKey(m.pubkey).bech32()))
        console.print(table)
        if m.relays is not None:
            table = Table("relay")
            for url in m.relays:
                table.add_row(url)
            console.print(table)
    elif "nprofile" in objects:
        pubkey, relays = nprofile_decode(objects)
        table = Table("key", "value")
        table.add_row("pubkey", pubkey)
        table.add_row("npub", str(PublicKey(pubkey).bech32()))
        for i in range(len(relays)):
            table.add_row(f"relay{i}", relays[i])
        console.print(table)
    elif "npub" in objects:
        pubkey = PublicKey.from_npub(objects)
        table = Table("key", "value")
        table.add_row("pubkey", pubkey.hex())
        table.add_row("npub", str(pubkey.bech32()))
        console.print(table)


@app.callback()
def main(verbose: int = 3):
    """Python CLI for nostr, enjoy."""
    # Logging
    state["verbose"] = verbose
    log = logging.getLogger(__name__)
    verbosity = ["critical", "error", "warn", "info", "debug"][int(min(verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)


if __name__ == "__main__":
    app()
