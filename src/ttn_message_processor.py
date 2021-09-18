# -*- coding: utf-8 -*-
import json
from logging import getLogger
from multiprocessing import Queue
from pathlib import Path

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "1.0.0"
__script__: Path = Path(__file__)
__script_name__: str = __script__.name
__script_path__: Path = __script__.parent

log = getLogger(__script_name__)


class TTNMessageProcessor:
    def __init__(self, topic=None, queue=None) -> None:
        super().__init__()
        self.topic = topic or "v3/+/devices/+/up"
        self.queue = queue or Queue()

    def on_connect(self, client, userdata, flags, rc):
        """
        The callback for when the client receives a CONNACK response from the server.
        :param client:
        :param userdata:
        :param flags:
        :param rc:
        :return:
        """
        log.info("Connected to MQTT with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.topic)

    def parse_message(self, msg):
        message = json.loads(msg.payload.decode("utf-8", "ignore"))

        flat_message = {
            "application_id": message['end_device_ids']['application_ids']['application_id'],
            "device.id": message["end_device_ids"]["device_id"],
            "device.eui": message["end_device_ids"]["dev_eui"],
            "device.addr": message["end_device_ids"]["dev_addr"],
            "received_at": message["received_at"],
            "message.port": message["uplink_message"]["f_port"],
            "message.counter": message["uplink_message"]["f_cnt"],
            "gateway.id": message["uplink_message"]["rx_metadata"][0]["gateway_ids"][
                "gateway_id"
            ],
            "gateway.eui": message["uplink_message"]["rx_metadata"][0]["gateway_ids"][
                "eui"
            ],
            "lora.rssi": message["uplink_message"]["rx_metadata"][0]["rssi"],
            "lora.channel_rssi": message["uplink_message"]["rx_metadata"][0][
                "channel_rssi"
            ],
            "lora.snr": message["uplink_message"]["rx_metadata"][0]["snr"],
            "lora.bandwidth": message["uplink_message"]["settings"]["data_rate"][
                "lora"
            ]["bandwidth"],
            "lora.spreading_factor": message["uplink_message"]["settings"]["data_rate"][
                "lora"
            ]["spreading_factor"],
            "lora.frequency": message["uplink_message"]["settings"]["frequency"],
            "lora.consumed_airtime": message["uplink_message"]["consumed_airtime"],
        }
        payload = {
            f"data.{k}": v
            for k, v in message["uplink_message"]["decoded_payload"].items()
        }
        flat_message.update(payload)

        device_name = flat_message['device.id']
        flat_message = {
            f"{device_name}.{k}": v
            for k, v in flat_message.items()
        }
        flat_message["application_id"] = flat_message[f"{device_name}.application_id"]
        flat_message["received_at"] = flat_message[f"{device_name}.received_at"]
        flat_message.pop(f"{device_name}.application_id")

        return flat_message

    def on_message(self, client, userdata, msg):
        """
        The callback for when a PUBLISH message is received from the server.
        :param client:
        :param userdata:
        :param msg:
        :return:
        """
        log.debug(f"Got message: {msg.topic} - {str(msg.payload)}")
        try:
            message = self.parse_message(msg)
            self.queue.put(message)
        except:
            log.error(f"Unable to parse message: {msg}")

    def on_log(self, client, userdata, level, buf):
        log.debug(buf)
