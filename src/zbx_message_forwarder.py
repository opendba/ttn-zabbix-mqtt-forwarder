# -*- coding: utf-8 -*-
from multiprocessing import Queue, Event
from pathlib import Path
from logging import getLogger

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "1.0.0"
__script__: Path = Path(__file__)
__script_name__: str = __script__.name
__script_path__: Path = __script__.parent

from queue import Empty

from threading import Thread
from typing import Optional, Callable, Any, Iterable, Mapping

from dateutil import parser
from pyzabbix import ZabbixMetric, ZabbixSender

log = getLogger(__script_name__)


class ZabbixMessageForwarder(Thread):
    def __init__(
        self,
        queue: Queue = None,
        zbx_host=None,
        zbx_port=None,
        shutdown_signal: Event = None,
    ) -> None:
        super().__init__()
        self.queue: Queue = queue or Queue()
        self.zbx_host: str = zbx_host
        self.zbx_port: int = zbx_port
        self.shutdown_signal: Event = shutdown_signal

    def run(self) -> None:
        log.debug("Start waiting for messages")
        while not self.shutdown_signal.is_set():
            try:
                source_message: dict = self.queue.get(timeout=5, block=True)
            except Empty:
                continue

            log.debug("Got message")
            message = source_message.copy()
            hostname: str = message.pop("application_id")
            received_at: str = message.pop("received_at")

            time = int(parser.isoparse(received_at).timestamp())

            zbx_data = [
                ZabbixMetric(hostname, k, v, clock=time) for k, v in message.items()
            ]
            try:
                result = ZabbixSender(
                    zabbix_server=self.zbx_host, zabbix_port=self.zbx_port
                ).send(zbx_data)
                log.debug(f"Send to zabbix: {result}")
            except ConnectionResetError as e:
                log.fatal(f"Failed to send data to zabbix: {e}")
                # put message back to the queue
                # TODO: make priority queue so that same message is picked up again
                self.queue.put(source_message)
        log.debug("Done waiting for messages")
