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
        message_callback_url=False,
    ) -> None:
        super().__init__(
            url,
            policy,
            message_pool,
            timeout,
            close_on_eose,
            message_callback,
            message_callback_url,
        )
        self.ws = None
        self.io_loop = io_loop
        self.running = True

    @property
    def is_connected(self) -> bool:
        return self.ws is not None and self.ws.protocol is not None

    @gen.coroutine
    def connect(self):
        error = False
        timeout_error = False
        self.error_counter = 0
        self.timeout_error_counter = 0
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
            # self.io_loop.call_later(1, self.send_message, self.request)
            while True:
                if self.outgoing_messages.qsize() > 0:
                    message = self.outgoing_messages.get()
                    self.num_sent_events += 1
                    self.ws.write_message(message)
                message = yield self.ws.read_message()
                if message is None:
                    break
                self._on_message(message)
                if not self.connected:
                    break

        except gen.TimeoutError:
            log.info(f"Timeout connecting to {self.url}")
            timeout_error = True
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
        elif timeout_error:
            self.timeout_error_counter += 1
            if self.timeout_error_counter <= self.timeout_error_threshold:
                self.io_loop.call_later(1, self.connect)
            else:
                return

        log.info(f"WebSocket connection to {self.url} closed")

    @gen.coroutine
    def _eose_received(self):
        self.eose_counter += 1
        if self.close_on_eose and self.eose_counter >= self.eose_threshold:
            yield self.close()

    @gen.coroutine
    def on_error(self):
        self.error_counter += 1
        if self.error_counter > self.error_threshold:
            yield self.close()

    @gen.coroutine
    def start(self):
        yield self.connect()

    @gen.coroutine
    def close(self):
        if self.ws is not None:
            self.connected = False
            self.error_counter = 0
            self.timeout_error_counter = 0
            yield self.ws.close()
            # self.io_loop.stop()
