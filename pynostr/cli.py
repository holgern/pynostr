import logging

import click
import typer

from pynostr.key import PrivateKey, PublicKey

log = logging.getLogger(__name__)
app = typer.Typer()

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
