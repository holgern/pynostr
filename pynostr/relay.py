import logging

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketError, websocket_connect

from .base_relay import BaseRelay, RelayPolicy
from .message_pool import MessagePool

log = logging.getLogger(__name__)


class Relay(BaseRelay):
    def __init__(
        self,
        url: str,
        message_pool: MessagePool,
        io_loop: IOLoop,
        policy: RelayPolicy = RelayPolicy(),
        timeout: float = 2.0,
        close_on_eose: bool = True,
        message_callback=None,
    ) -> None:
        super().__init__(
            url,
            message_pool,
            policy,
            None,
            None,
            timeout,
            close_on_eose,
            message_callback,
        )
        self.io_loop = io_loop
        self.running = True

    @property
    def is_connected(self) -> bool:
        return self.ws is not None and self.ws.protocol is not None

    @gen.coroutine
    def connect(self):
        error = False
        try:
            if self.timeout > 0:
                self.ws = yield gen.with_timeout(
                    self.io_loop.time() + self.timeout,
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
            self.connected = True
            # yield self.ws.write_message(self.request)
            self.publish(self.request)
            # self.io_loop.call_later(1, self.send_message, self.request)
            while True:
                if self.outgoing_messages.qsize() > 0:
                    message = self.outgoing_messages.get()
                    self.num_sent_events += 1
                    yield self.ws.write_message(message)
                message = yield self.ws.read_message()
                if message is None:
                    break
                self._on_message(message)
                if not self.connected:
                    break

        except gen.TimeoutError:
            log.warning("Timeout connecting to", self.url)
            error = True
        except WebSocketError as e:
            log.warning(f"Error connecting to WebSocket server at {self.url}: {e}")
            error = True
        except Exception as e:
            log.warning(f"Error connecting to {self.url}: {e}")
            error = True
        if error:
            self.error_counter += 1
            if self.error_counter <= self.error_threshold:
                self.io_loop.call_later(1, self.connect)
            else:
                return
        # print(self.request)
        # self.publish(self.request)

        log.info(f"WebSocket connection to {self.url} closed")

    def _eose_received(self):
        if self.close_on_eose:
            self.close()

    @gen.coroutine
    def start(self):
        yield self.connect()

    @gen.coroutine
    def close(self):
        if self.ws is not None:
            self.connected = False
            self.error_counter = 0
            yield self.ws.close()
            # self.io_loop.stop()
