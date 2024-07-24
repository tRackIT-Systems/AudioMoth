import argparse
import logging
import struct
from dataclasses import dataclass
from typing import Any, Callable

import hid

from audiomoth.utils import (
    HID_CONFIGURATION_MESSAGE,
    HID_PERSIST_MESSAGE,
    HID_READ_MESSAGE,
    HID_RESTORE_MESSAGE,
    _parse_args,
    _setup_logging,
    _validate_parameter,
)


@dataclass
class AudioMothConfig:
    time: int = 0  # uint32_t
    gain: int = 2  # uint8_t
    clock_divider: int = 4  # uint8_t
    acquisition_cycles: int = 16  # uint8_t
    oversamplerate: int = 1  # uint8_t
    samplerate: int = 384000  # uint32_t
    samplerate_divider: int = 1  # uint8_t
    lower_filter_freq: int = 0  # uint16_t
    higher_filter_freq: int = 0  # uint16_t


def get_all_usb_devices() -> list[dict[str, Any]]:
    """Get all attached USB HID devices

    Returns:
        list[dict[str, Any]]: List containing all attached USB HID devices
    """
    return hid.enumerate()


def get_audiomoth_device(
    serial_number: str | None = None,
) -> dict[str, Any]:
    """Get an AudioMoth device attached via USB

    Args:
        serial_number (str | None): Serial number of devive to get. If not given and multiple devices are connected, the first device will be returned

    Raises:
        RuntimeError: Raised if no device found (with the given serial number, if provided)

    Returns:
        dict[str, Any]: Dictionary containing USB HID information
    """
    devices: list[dict[str, Any]] = [
        device for device in hid.enumerate() if "product_string" in device and "AudioMoth" in device["product_string"]
    ]

    if len(devices) == 0:
        raise RuntimeError("Can not find any AudioMoth")

    if serial_number is not None:
        device: dict[str, Any] | None = next(
            (device for device in devices if "serial_number" in device and device["serial_number"] == serial_number),
            None,
        )
        if device is None:
            raise RuntimeError(f"Can not find AudioMoth with serial number {serial_number}")

    return devices[0]


def get_config(serial_number: str | None = None) -> AudioMothConfig:
    """Get current configuration of the AudioMoth

    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be returned

    Raises:
        RuntimeError: Raised if the configuration could not be read

    Returns:
        AudioMothConfig: Dataclass containing the config
    """
    audio_moth: dict[str, Any] = get_audiomoth_device(serial_number)

    with hid.Device(
        vid=audio_moth["vendor_id"],
        pid=audio_moth["product_id"],
        serial=audio_moth["serial_number"],
    ) as device:
        device.write(HID_READ_MESSAGE)
        read_data: bytes = device.read(18)
        unpacked_data: tuple[Any] = struct.unpack("<BLBBBBLBHH", read_data)
        if unpacked_data[0] != HID_READ_MESSAGE[0]:
            raise RuntimeError(
                f"Could not read configuration from device [{audio_moth["serial_number"]=}, [{unpacked_data[0]=}, {HID_READ_MESSAGE=}]"
            )

        return AudioMothConfig(
            time=unpacked_data[1],
            gain=unpacked_data[2],
            clock_divider=unpacked_data[3],
            acquisition_cycles=unpacked_data[4],
            oversamplerate=unpacked_data[5],
            samplerate=unpacked_data[6],
            samplerate_divider=unpacked_data[7],
            lower_filter_freq=unpacked_data[8],
            higher_filter_freq=unpacked_data[9],
        )


def set_config(
    serial_number: str | None = None,
    gain: int | None = None,
    clock_divider: int | None = None,
    acquisition_cycles: int | None = None,
    oversamplerate: int | None = None,
    samplerate: int | None = None,
    samplerate_divider: int | None = None,
    lower_filter_freq: int | None = None,
    higher_filter_freq: int | None = None,
) -> AudioMothConfig:
    """Set specific configurations to device with serial number.
    Only the values provided as arguments are changed. All other configuration parameters remain unchanged.

    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be changed
        gain (int | None): Gain value to set
        clock_divider (int | None): Cloc devider to set
        acquisition_cycles (int | None): Acquisition cycles to set
        oversamplerate (int | None): Oversamplerate to set
        samplerate (int | None): Samplerate to set
        samplerate_divider (int | None): Samplerate divider to set
        lower_filter_freq (int | None): Lower frequency filter to set
        higher_filter_freq (int | None): Higher frequency filter to set

    Raises:
        ValueError: Parameters are validated to comply with the AudioMoth docs. If validation failes, a ValueError is raised

    Returns:
        AudioMothConfig: Returns newly set configuration
    """
    audio_moth: dict[str, Any] = get_audiomoth_device(serial_number)
    old_cfg: AudioMothConfig = get_config(serial_number)

    for param, value in locals().items():
        if param != "audio_moth" and param != "old_cfg" and param != "serial_number" and value is not None:
            sr = samplerate if samplerate is not None else old_cfg.samplerate
            try:
                _validate_parameter(param, value, sr)
            except ValueError as e:
                raise ValueError(e)
            setattr(old_cfg, param, value)

    with hid.Device(
        vid=audio_moth["vendor_id"],
        pid=audio_moth["product_id"],
        serial=audio_moth["serial_number"],
    ) as device:
        data: bytes = struct.pack(
            "<BLBBBBLBHH",
            HID_CONFIGURATION_MESSAGE[0],
            old_cfg.time,
            old_cfg.gain,
            old_cfg.clock_divider,
            old_cfg.acquisition_cycles,
            old_cfg.oversamplerate,
            old_cfg.samplerate,
            old_cfg.samplerate_divider,
            old_cfg.lower_filter_freq,
            old_cfg.higher_filter_freq,
        )
        device.write(data)

        return old_cfg


def restore_config(serial_number: str | None = None) -> None:
    """Restore the persistent configuration

    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be restored
    """
    audio_moth: dict[str, Any] = get_audiomoth_device(serial_number)

    with hid.Device(
        vid=audio_moth["vendor_id"],
        pid=audio_moth["product_id"],
        serial=audio_moth["serial_number"],
    ) as device:
        device.write(HID_RESTORE_MESSAGE)


def persist_config(serial_number: str | None = None) -> None:
    """Persist the temporary configuration

    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be persisted.
    """
    audio_moth: dict[str, Any] = get_audiomoth_device(serial_number)

    with hid.Device(
        vid=audio_moth["vendor_id"],
        pid=audio_moth["product_id"],
        serial=audio_moth["serial_number"],
    ) as device:
        device.write(HID_PERSIST_MESSAGE)


def main():
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


if __name__ == "__main__":
    main()
