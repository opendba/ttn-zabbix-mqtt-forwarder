# -*- coding: utf-8 -*-
import logging
import sys
from logging import getLogger
from pathlib import Path

__author__ = "Edgars Cupits (edgars@opendba.lv)"
__version__ = "1.0.0"
__script__: Path = Path(__file__)
__script_name__: str = __script__.name
__script_path__: Path = __script__.parent

log = getLogger(__script_name__)


def configure_logging(debug=False, log_name=None, log_format=None):
    log_level = logging.DEBUG
    if not log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if not debug:
        for logger_name in []:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        log_level = logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_name:
        handlers.append(logging.FileHandler(f"{log_name}", mode="a"))

    logging.basicConfig(
        format=log_format, level=log_level, handlers=handlers,
    )
