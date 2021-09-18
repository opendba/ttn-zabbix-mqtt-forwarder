# -*- coding: utf-8 -*-
from multiprocessing import Queue
from pathlib import Path
from logging import getLogger

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "1.0.0"
__script__: Path = Path(__file__)
__script_name__: str = __script__.name
__script_path__: Path = __script__.parent

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
        zbx_port=None
    ) -> None:
        super().__init__()
        self.queue = queue or Queue()
        self.zbx_host = zbx_host
        self.zbx_port = zbx_port

    def run(self) -> None:
        while True:
            message: dict = self.queue.get()
            log.debug("Got message")

            hostname: str = message.pop('application_id')
            received_at: str = message.pop("received_at")

            time = int(parser.isoparse(received_at).timestamp())

            zbx_data = [
                ZabbixMetric(hostname, k, v, clock=time) for k, v in message.items()
            ]
            result = ZabbixSender(
                zabbix_server=self.zbx_host, zabbix_port=self.zbx_port
            ).send(zbx_data)
            log.debug(f"Send to zabbix: {result}")
