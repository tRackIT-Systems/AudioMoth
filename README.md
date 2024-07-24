# AudioMoth

Simple tool to configure your AudioMoth

## Installation
### Requirements
This library has one dependency, [hid](https://pypi.org/project/hid/).
However, in order for `hid` to work you need the `hidapi` library.
Please install according to your operating system (more info on their [Github page](https://github.com/libusb/hidapi)).

Furthermore, `AudioMoth` requires Python 3.12.

If `hidapi` is installed, install `AudioMoth` using you favorite Python package management tool such as `pip`, `rye` or `pdm`.
However, `AudioMoth` is not published, so you have to use the URL, i.e.:

```sh
#pip
pip install "git+https://github.com/trackit-systems/audiomoth"
#rye
rye add audiomoth --git https://github.com/trackit-systems/audiomoth
#pdm
pdm add "git+https://github.com/trackit-systems/audiomoth"
```

## Usage
This project can be used as a CLI tool or as a library.

### Library usage
The library contains six functions.

```python
def get_all_usb_devices() -> list[dict[str, Any]]:
    Get all attached USB HID devices
    Returns:
        list[dict[str, Any]]: List containing all attached USB HID devices


def get_audiomoth_device(serial_number: str | None = None) -> dict[str, Any]:
    Get an AudioMoth device attached via USB
    Args:
        serial_number (str | None): Serial number of devive to get. If not given and multiple devices are connected, the first device will be returned
    Raises:
        RuntimeError: Raised if no device found (with the given serial number, if provided)
    Returns:
        dict[str, Any]: Dictionary containing USB HID information


def get_config(serial_number: str | None = None) -> AudioMothConfig:
    Get current configuration of the AudioMoth
    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be returned
    Raises:
        RuntimeError: Raised if the configuration could not be read
    Returns:
        AudioMothConfig: Dataclass containing the config


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
    Set specific configurations to device with serial number.
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
        ValueError: Raised a configuration could not be set
    Returns:
        AudioMothConfig: Returns newly set configuration


def restore_config(serial_number: str | None = None) -> None:
    Restore the persistent configuration
    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be restored


def persist_config(serial_number: str | None = None) -> None:
    Persist the temporary configuration
    Args:
        serial_number (str | None): Serial number of the device to use. If not given and multiple devices are connected, the configuration of the first device will be persisted.
```

### CLI usage
#### Basic usage
AudioMoth consists of six commands as well as two optional parameters:

```
usage: AudioMoth [-h] [-l {DEBUG,INFO,WARN,ERROR}] [-s SERIAL_NUMBER] {list,moths,restore,persist,get,set} ...

AudioMoth configuration tool

positional arguments:
  {list,moths,restore,persist,get,set}
    list                List all devices
    moths               List all AudioMoth devices
    restore             Restore the persisted config
    persist             Persist the in-memory config
    get                 Get or set config
    set                 Get or set config

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARN,ERROR}, --log_level {DEBUG,INFO,WARN,ERROR}
                        Level for logging [DEBUG, INFO, WARN, ERROR]
  -s SERIAL_NUMBER, --serial_number SERIAL_NUMBER
                        Serial number of the AudioMoth to use
```

#### `list` command
The `list` command shows all attached USB HID devices.

```
usage: AudioMoth list [-h]

options:
  -h, --help  show this help message and exit
```

#### `moths` command
The `moths` command shows all attached AudioMoth devices.

```
usage: AudioMoth moths [-h]

options:
  -h, --help  show this help message and exit
```

#### `restore` command
The `restore` command restores the temporary in-memory configuration with the persisted configuration.

```
usage: AudioMoth restore [-h]

options:
  -h, --help  show this help message and exit
```

#### `persist` command
The `persist` command persists the temporary in-memory configuration.

```
usage: AudioMoth persist [-h]

options:
  -h, --help  show this help message and exit
```

#### `get` command
The `get` command shows the currently active, in-memory nconfiguration.

```
usage: AudioMoth get [-h]

options:
  -h, --help  show this help message and exit
```

#### `set` command
The `set` command sets the configuration given and activates it as the active in-memory configuration

```
usage: AudioMoth set [-h] [-g {0,1,2,3,4}] [-c CLOCK_DIVIDER] [-a ACQUISITION_CYCLES] [-o OVERSAMPLERATE]
                     [-s {8000,16000,32000,48000,96000,192000,250000,384000}] [-d SAMPLERATE_DIVIDER] [-l LOWER_FILTER_FREQ] [-f HIGHER_FILTER_FREQ]

options:
  -h, --help            show this help message and exit
  -g {0,1,2,3,4}, --gain {0,1,2,3,4}
                        Set gain
  -c CLOCK_DIVIDER, --clock_divider CLOCK_DIVIDER
                        Set clock divider
  -a ACQUISITION_CYCLES, --acquisition_cycles ACQUISITION_CYCLES
                        Set acquisition cycles
  -o OVERSAMPLERATE, --oversamplerate OVERSAMPLERATE
                        Set oversamplerate
  -s {8000,16000,32000,48000,96000,192000,250000,384000}, --samplerate {8000,16000,32000,48000,96000,192000,250000,384000}
                        Set samplerate
  -d SAMPLERATE_DIVIDER, --samplerate_divider SAMPLERATE_DIVIDER
                        Set samplerate divider
  -l LOWER_FILTER_FREQ, --lower_filter_freq LOWER_FILTER_FREQ
                        Set lower filter frequency
  -f HIGHER_FILTER_FREQ, --higher_filter_freq HIGHER_FILTER_FREQ
                        Set higher filter frequency
```