"""Forked from https://github.com/jeffthibault/python-nostr.git."""
import threading
import time
from typing import Union

from websocket import WebSocketApp

from .base_relay import BaseRelay, RelayPolicy, RelayProxyConnectionConfig
from .message_pool import MessagePool


class Relay(BaseRelay):
    def __init__(
        self,
        url: str,
        message_pool: MessagePool,
        policy: RelayPolicy = RelayPolicy(),
        ssl_options: dict = None,
        proxy_config: Union[None, RelayProxyConnectionConfig] = None,
    ) -> None:
        super().__init__(url, message_pool, policy, ssl_options, proxy_config)
        self.ws: WebSocketApp = WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

    @property
    def is_connected(self) -> bool:
        return False if self.ws.sock is None else self.ws.sock.connected

    def open_connections(self, ssl_options: dict = None):
        if ssl_options is None:
            ssl_options = {}
        self.ssl_options = ssl_options
        if not self.is_connected:
            threading.Thread(target=self.connect, name=f"{self.url}-thread").start()
        time.sleep(2)
        assert self.is_connected
        self._is_connected = True

    def close(self):
        if self.ws.sock is not None:
            self.ws.close()

    def close_connections(self):
        self.close()

    def connect(self):
        self.ws.run_forever(
            sslopt=self.ssl_options,
            http_proxy_host=None
            if self.proxy_config is None
            else self.proxy_config.host,
            http_proxy_port=None
            if self.proxy_config is None
            else self.proxy_config.port,
            proxy_type=None if self.proxy_config is None else self.proxy_config.type,
        )

    def check_reconnect(self):
        try:
            self.close()
        except Exception:
            pass
        self.connected = False
        if self.reconnect:
            time.sleep(1)
            self.connect()

    def publish(self, message: str):
        if self.connected:
            self.ws.send(message)

    def _on_open(self, class_obj):
        self.connected = True

    def _on_close(self, class_obj, status_code, message):
        self.connected = False

    def _on_message(self, class_obj, message: str):
        if message is None:
            print("Empty message received")
        else:
            if self._is_valid_message(message):
                self.message_pool.add_message(message, self.url)

    def _on_error(self, class_obj, error):
        self.connected = False
        self.error_counter += 1
        if self.error_threshold and self.error_counter > self.error_threshold:
            pass
        else:
            self.check_reconnect()
