import argparse
import logging
from typing import Callable

from utils import _parse_args, _setup_logging

from audiomoth import (
    get_all_usb_devices,
    get_audiomoth_device,
    get_config,
    persist_config,
    restore_config,
    set_config,
)

if __name__ == "__main__":
    args: argparse.Namespace = _parse_args()

    cmds: dict[str, Callable] = {
        "list": get_all_usb_devices,
        "moths": get_audiomoth_device,
        "get": get_config,
        "set": set_config,
        "restore": restore_config,
        "persist": persist_config,
    }

    _setup_logging(args.log_level)
    logger: logging.Logger = logging.getLogger(__name__)

    func: Callable | None = cmds.get(args.command, None)
    if func is None:
        logger.error(f"Command not supported [{func=}]")
        exit(1)

    if args.command == "list":
        logger.info(func())
    elif args.command == "set":
        func(
            args.serial_number,
            args.gain,
            args.clock_divider,
            args.acquisition_cycles,
            args.oversamplerate,
            args.samplerate,
            args.samplerate_divider,
            args.lower_filter_freq,
            args.higher_filter_freq,
        )
    elif args.command in ["persist", "restore"]:
        func(serial_number=args.serial_number)
    elif args.command in ["moths", "get"]:
        logger.info(func(serial_number=args.serial_number))
