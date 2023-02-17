import json
from typing import Union

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketError, websocket_connect

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
        self.running = True

    @property
    def is_connected(self) -> bool:
        return self.ws is not None

    @gen.coroutine
    def connect(self, timeout=2):
        try:
            if timeout > 0:
                self.ws = yield gen.with_timeout(
                    self.io_loop.time() + 2,
                    websocket_connect(
                        self.url,
                        ping_interval=60,
                        ping_timeout=120,
                    ),
                )
            else:
                self.ws = yield websocket_connect(
                    self.url,
                    ping_interval=60,
                    ping_timeout=120,
                )
            # yield self.ws.write_message(self.request)
            self.publish(self.request)
            # self.io_loop.call_later(1, self.send_message, self.request)
            while True:
                message = yield self.ws.read_message()
                if message is None:
                    break
                if not self.on_message(message):
                    break

        except gen.TimeoutError:
            print("Timeout connecting to", self.url)
            return
        except WebSocketError as e:
            print(f"Error connecting to WebSocket server at {self.url}: {e}")
            return
        except Exception as e:
            print(f"Error connecting to {self.url}: {e}")
            return
        # print(self.request)
        # self.publish(self.request)

        # print(f"WebSocket connection to {self.url} closed")

    def on_message(self, message):
        if self._is_valid_message(message):
            message_json = json.loads(message)
            message_type = message_json[0]
            if message_type == RelayMessageType.EVENT:
                # event = Event.from_dict(message_json[2])
                # print(event.to_message())
                self.message_pool.add_message(message, self.url)
            elif message_type == RelayMessageType.END_OF_STORED_EVENTS:
                self.close()
                self.message_pool.add_message(message, self.url)
                return False
        return True
        # yield None

    @gen.coroutine
    def start(self):
        yield self.connect()

    @gen.coroutine
    def close(self):
        if self.ws is not None:
            yield self.ws.close()
            # self.io_loop.stop()

    @gen.coroutine
    def publish(self, message: str):
        # print(message)
        yield self.ws.write_message(message)

    def send_message(self, message):
        gen.maybe_future(self.ws.write_message(message))
