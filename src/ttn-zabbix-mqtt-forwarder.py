# -*- coding: utf-8 -*-
import os
from logging import getLogger, Logger
from multiprocessing import Queue, Event
from pathlib import Path
from time import sleep
from typing import Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "0.1.0"
__script_name__ = os.path.splitext(os.path.basename(__file__))[0]
__script_path__ = os.path.dirname(__file__)

# logging settings
__project_path__ = Path(f"{__script_path__}/../").resolve()

from src.log_utils import configure_logging
from src.signal_watcher import SignalWatcher
from src.ttn_message_processor import TTNMessageProcessor
from src.zbx_message_forwarder import ZabbixMessageForwarder

data_dir = __project_path__.joinpath("data")
log_dir = __project_path__.joinpath("log")

log_file = log_dir.joinpath(f"{__script_name__}.log")
log_format = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
log: Optional[Logger] = None


def main():
    global log, log_format, log_file
    shutdown_signal = Event()
    shutdown_signal.clear()

    load_dotenv(dotenv_path=__project_path__.joinpath(".env"), verbose=False)

    debug_mode = os.environ.get("DEBUG", "").lower() == "true"
    json_log = os.environ.get("LOG_FORMAT", "").lower() == "json"
    log_persist = os.environ.get("LOG_PERSIST", "").lower() == "true"
    if json_log:
        log_format = (
            "{ "
            '"time": "%(asctime)s", '
            '"level": "%(levelname)s", '
            '"module": "%(module)s", '
            '"message": "%(message)s" '
            "}"
        )

    log = getLogger(__script_name__)
    # if log persistance is not needed, don't log to file
    if not log_persist:
        log_file = None
    configure_logging(
        debug=debug_mode, log_name=log_file, log_format=log_format,
    )

    if debug_mode:
        log.debug("Dumping all env variables:")
        for k, v in os.environ.items():
            if "MQTT_" in k or "ZBX" in k or "DEBUG" in k:
                log.debug(f"{k}:{v}")

    log.info("Starting {0} v {1}".format(__script_name__, __version__))

    zbx_host = os.environ.get("ZBX_HOST")
    zbx_port = int(os.environ.get("ZBX_PORT", "10051"))

    if not zbx_host:
        log.debug("Zabbix host is not defined")
        exit(-1)

    message_queue = Queue()

    zbx_forwarder = ZabbixMessageForwarder(
        queue=message_queue,
        zbx_host=zbx_host,
        zbx_port=zbx_port,
        shutdown_signal=shutdown_signal,
    )
    ttn_processor = TTNMessageProcessor(queue=message_queue)

    zbx_forwarder.start()

    client = mqtt.Client()
    client.on_connect = ttn_processor.on_connect
    client.on_message = ttn_processor.on_message
    client.on_log = ttn_processor.on_log

    mqtt_host = os.environ.get("MQTT_HOST") or "eu1.cloud.thethings.network"
    mqtt_port = int(os.environ.get("MQTT_PORT") or 8883)

    mqtt_username = os.environ.get("MQTT_USERNAME")
    mqtt_password = os.environ.get("MQTT_PASSWORD")

    if mqtt_username:
        client.username_pw_set(mqtt_username, mqtt_password)
    mqtt_tls = False
    if os.environ.get("MQTT_TLS", "").lower() == "true":
        mqtt_tls = True
        client.tls_set()
    log.info(
        f"Connecting to MQTT: {mqtt_username}@{mqtt_host}:{mqtt_port} ({'tls' if mqtt_tls else 'no tls'})"
    )
    client.connect(
        mqtt_host, mqtt_port, keepalive=int(os.environ.get("MQTT_KEEPALIVE", 30))
    )
    log.info(f"Using zabbix: {zbx_host}:{zbx_port}")

    _ = SignalWatcher(shutdown_signal=shutdown_signal)
    client.loop_start()
    while not shutdown_signal.is_set():
        sleep(5)
    client.disconnect()
    client.loop_stop(force=True)

    # all good
    exit_code = 0
    if exit_code == 0:
        log.info("All good. No errors found.")
    else:
        log.fatal("Execution failed")

    # return exit code to OS
    exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.fatal(e.args)
        raise
