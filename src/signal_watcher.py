# -*- coding: utf-8 -*-
import signal
from multiprocessing import Event
from pathlib import Path
from logging import getLogger

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "1.0.0"
__script__: Path = Path(__file__)
__script_name__: str = __script__.name
__script_path__: Path = __script__.parent

log = getLogger(__script_name__)


class SignalWatcher:
    def __init__(self, shutdown_signal: Event):
        self.shutdown_signal: Event = shutdown_signal
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        log.debug("Got shutdown signal")
        self.shutdown_signal.set()
