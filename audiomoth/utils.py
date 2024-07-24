import argparse
import logging
import logging.handlers

HID_CONFIGURATION_MESSAGE = bytes([0x01])
HID_RESTORE_MESSAGE = bytes([0x04])
HID_READ_MESSAGE = bytes([0x05])
HID_PERSIST_MESSAGE = bytes([0x06])


def _validate_parameter(parameter: str, value: int, sr: int) -> None:
    """AudioMoth has requirements to its configuration, especially for the gain, samplerate and band pass filters.
    Gain must be in [0, 1, 2, 3, 4], samplerate in [8000, 16000, 32000, 48000, 96000, 192000, 250000, 384000] and
    band pass filters must be divisible by 100 and not bigger than half of samplerate. Furthermore, each value has
    to be an integer.

    Args:
        parameter (str): Name of parameter to check
        value (int): Value of the parameter to check
        sr (int): Current samplerate of the AudioMoth. Only used for band pass filters.

    Raises:
        ValueError: Raised of one of the above conditions is not met.
    """
    if not isinstance(value, int):
        raise ValueError(f"Parameter {parameter} must be of type int, is {type(value)}")

    match parameter:
        case "gain":
            if value not in [0, 1, 2, 3, 4]:
                raise ValueError(f"gain must on of [0, 1, 2, 3, 4], is {value}")
        case "samplerate":
            if value not in [8000, 16000, 32000, 48000, 96000, 192000, 250000, 384000]:
                raise ValueError(
                    f"samplerate must on of [8000, 16000, 32000, 48000, 96000, 192000, 250000, 384000], is {value}"
                )
        case "lower_filter_freq" | "higher_filter_freq":
            if value % 100 != 0 or value > int(sr / 2):
                raise ValueError(
                    f"band pass filters must be divisible by 100 and not bigger than half of samplerate, is {value}, samplerate is {sr}"
                )


class ColoredFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey: str = "\033[0;37m"
    blue: str = "\x1b[38;5;39m"
    yellow: str = "\x1b[38;5;226m"
    red: str = "\x1b[38;5;196m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"
    fmt: str = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

    def __init__(self) -> None:
        super().__init__()
        self.FORMATS: dict[int, str] = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record) -> str:
        log_fmt: str = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Ignore event messages from inotify
        inotify_message: bool = not record.getMessage().startswith("Events received")
        # Ignore the very verbose output of batdetects internals
        batdetect_name: bool = not record.name.startswith("numba.core")
        return inotify_message and batdetect_name


def _setup_logging(log_level: str, log_file: str | None = None) -> None:
    logger: logging.Logger = logging.getLogger()
    logger.setLevel(log_level.upper())

    # Create stdout handler for logging to the console
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(log_level.upper())
    stdout_handler.setFormatter(ColoredFormatter())
    stdout_handler.addFilter(LoggingFilter())
    logger.addHandler(stdout_handler)

    if log_file is not None:
        # Create stdout handler for logging to the console
        # Retain 200 files each max 5MB, i.e., creating up to 1GB log files
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=200)
        file_handler.setLevel(log_level.upper())
        file_handler.setFormatter(ColoredFormatter())
        file_handler.addFilter(LoggingFilter())
        logger.addHandler(file_handler)


def _parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="AudioMoth",
        description="AudioMoth configuration tool",
    )
    parser.add_argument(
        "-l",
        "--log_level",
        required=False,
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Level for logging [DEBUG, INFO, WARN, ERROR]",
    )

    parser.add_argument(
        "-s",
        "--serial_number",
        help="Serial number of the AudioMoth to use",
        required=False,
        type=str,
    )

    subparsers: argparse._SubParsersAction = parser.add_subparsers(dest="command")
    list_parser: argparse.ArgumentParser = subparsers.add_parser("list", help="List all devices")  # noqa: F841
    moths_parser: argparse.ArgumentParser = subparsers.add_parser("moths", help="List all AudioMoth devices")  # noqa: F841
    restore_parser: argparse.ArgumentParser = subparsers.add_parser("restore", help="Restore the persisted config")  # noqa: F841
    persist_parser: argparse.ArgumentParser = subparsers.add_parser("persist", help="Persist the in-memory config")  # noqa: F841
    get_conf_parser: argparse.ArgumentParser = subparsers.add_parser("get", help="Get or set config")  # noqa: F841
    set_conf_parser: argparse.ArgumentParser = subparsers.add_parser("set", help="Get or set config")
    set_conf_parser.add_argument(
        "-g",
        "--gain",
        help="Set gain",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-c",
        "--clock_divider",
        help="Set clock divider",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-a",
        "--acquisition_cycles",
        help="Set acquisition cycles",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-o",
        "--oversamplerate",
        help="Set oversamplerate",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-s",
        "--samplerate",
        help="Set samplerate",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-d",
        "--samplerate_divider",
        help="Set samplerate divider",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-l",
        "--lower_filter_freq",
        help="Set lower filter frequency",
        type=int,
        required=False,
    )
    set_conf_parser.add_argument(
        "-f",
        "--higher_filter_freq",
        help="Set higher filter frequency",
        type=int,
        required=False,
    )

    return parser.parse_args()
