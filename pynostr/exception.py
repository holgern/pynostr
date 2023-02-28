class RelayException(Exception):
    pass


class NIPValidationException(Exception):
    """Raised when a specific event does not meet NIP requirements."""
