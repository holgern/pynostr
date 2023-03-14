"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import time
from threading import Thread
from typing import Union

from websocket import WebSocketApp

from .base_relay import BaseRelay, RelayPolicy, RelayProxyConnectionConfig
from .message_pool import MessagePool


class WebSocketRelay(BaseRelay):
    def __init__(
        self,
        url: str,
        message_pool: MessagePool,
        policy: RelayPolicy = RelayPolicy(),
        ssl_options: dict = None,
        proxy_config: Union[None, RelayProxyConnectionConfig] = None,
    ) -> None:
        super().__init__(url, policy, message_pool)
        self.ssl_options = ssl_options
        self.proxy_config = proxy_config
        self.ws: WebSocketApp = WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._connection_thread: Thread = None

    @property
    def is_connected(self) -> bool:
        with self.lock:
            if (
                self._connection_thread is None
                or not self._connection_thread.is_alive()
            ):
                return False
            else:
                return True

    def close(self):
        if self.is_connected:
            self.ws.close()

    def connect(self, is_reconnect=False):
        if not self.is_connected:
            with self.lock:
                self._connection_thread = Thread(
                    target=self.ws.run_forever,
                    kwargs={
                        "sslopt": self.ssl_options,
                        "http_proxy_host": self.proxy_config.host
                        if self.proxy_config is not None
                        else None,
                        "http_proxy_port": self.proxy_config.port
                        if self.proxy_config is not None
                        else None,
                        "proxy_type": self.proxy_config.type
                        if self.proxy_config is not None
                        else None,
                    },
                    name=f"{self.url}-connection",
                )
                self._connection_thread.start()

            if not is_reconnect:
                Thread(
                    target=self.outgoing_messages_worker,
                    name=f"{self.url}-outgoing-messages-worker",
                    daemon=True,
                ).start()

            time.sleep(1)

    def outgoing_messages_worker(self):
        while True:
            if self.is_connected:
                message = self.outgoing_messages.get()
                try:
                    self.ws.send(message)
                    self.num_sent_events += 1
                except Exception:
                    self.outgoing_messages.put(message)

    def _on_open(self, class_obj):
        pass

    def _on_close(self, class_obj, status_code, message):
        self.error_counter = 0

    def _on_error(self, class_obj, error):
        self.error_counter += 1
        if self.error_counter > self.error_threshold:
            self.close()
