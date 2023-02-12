import json
from typing import Union

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import websocket_connect

from .base_relay import BaseRelay, RelayPolicy, RelayProxyConnectionConfig
from .message_pool import MessagePool
from .message_type import RelayMessageType


class TornadoRelay(BaseRelay):
    def __init__(
        self,
        url: str,
        message_pool: MessagePool,
        io_loop: IOLoop,
        policy: RelayPolicy = RelayPolicy(),
        ssl_options: dict = None,
        proxy_config: Union[None, RelayProxyConnectionConfig] = None,
    ) -> None:
        super().__init__(url, message_pool, policy, ssl_options, proxy_config)
        self.io_loop = io_loop

    @property
    def is_connected(self) -> bool:
        return self.ws is not None

    @gen.coroutine
    def connect(self):
        yield websocket_connect(
            self.url,
            callback=self.maybe_retry_connection,
            on_message_callback=self.on_message,
            ping_interval=60,
            ping_timeout=120,
        )

    def maybe_retry_connection(self, future) -> None:
        try:
            self.ws = future.result()
            self.publish(self.request)
        except Exception:
            print("Could not reconnect, retrying in 3 seconds...")
            self.io_loop.call_later(3, self.connect)

    def on_message(self, message):
        if message is None:
            self.connect()
        else:
            if self._is_valid_message(message):
                message_json = json.loads(message)
                message_type = message_json[0]
                if message_type == RelayMessageType.EVENT:
                    # event = Event.from_dict(message_json[2])
                    # print(event.to_message())
                    self.message_pool.add_message(message, self.url)
                elif message_type == RelayMessageType.END_OF_STORED_EVENTS:
                    self.close()

    def start(self):
        self.connect()

    def close(self):
        if self.ws is not None:
            self.ws.close()
            self.io_loop.stop()

    def publish(self, message: str):
        # print(message)
        self.ws.write_message(message)
