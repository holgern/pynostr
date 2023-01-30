import logging

import click

from pynostr._version import __version__
from pynostr.key import PrivateKey, PublicKey

log = logging.getLogger(__name__)


@click.group(chain=True)
@click.option(
    '--verbose', '-v', default=3, help='Verbosity (0 = critical to 4 = debug)'
)
@click.version_option(version=__version__)
def main(verbose):
    """Python CLI for nostr, enjoy."""
    # Logging
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


@main.command()
def keygen():
    """Creates a private and public key."""
    private_key = PrivateKey()
    public_key = private_key.public_key
    click.echo(f"Private key: {private_key.bech32()}")
    click.echo(f"Public key: {public_key.bech32()}")


@main.command()
@click.argument('npub', type=str)
def convert(npub: str):
    """Converts npub key to hex."""
    public_key = PublicKey.from_npub(npub)
    click.echo(f"npub: {public_key.bech32()}")
    click.echo(f"hex: {public_key.hex()}")


if __name__ == "__main__":
    main()
