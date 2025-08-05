class ClientMessageType:
    EVENT = "EVENT"
    REQUEST = "REQ"
    CLOSE = "CLOSE"
    AUTH = "AUTH"
    COUNT = "COUNT"

    @staticmethod
    def is_valid(type: str) -> bool:
        if (
            type == ClientMessageType.EVENT
            or type == ClientMessageType.REQ
            or type == ClientMessageType.CLOSE
            or type == ClientMessageType.AUTH
            or type == ClientMessageType.COUNT
        ):
            return True
        return False


class RelayMessageType:
    EVENT = "EVENT"
    NOTICE = "NOTICE"
    AUTH = "AUTH"
    END_OF_STORED_EVENTS = "EOSE"
    OK = "OK"
    COUNT = "COUNT"

    @staticmethod
    def is_valid(type: str) -> bool:
        if (
            type == RelayMessageType.EVENT
            or type == RelayMessageType.NOTICE
            or type == RelayMessageType.AUTH
            or type == RelayMessageType.END_OF_STORED_EVENTS
            or type == RelayMessageType.OK
            or type == RelayMessageType.COUNT
        ):
            return True
        return False
