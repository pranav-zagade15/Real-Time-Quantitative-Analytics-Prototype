"""Minimal WebSocket client abstraction.

This is intentionally lightweight: the real project would implement robust
reconnects, buffering, and backpressure.
"""
from typing import Callable, Optional
import threading
import time


class WebsocketClient:
    def __init__(self, on_message: Callable[[dict], None], source: str = "binance"):
        self.on_message = on_message
        self.source = source
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _run_loop(self):
        # Placeholder: in production, connect to Binance websockets
        while self._running:
            time.sleep(1.0)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
