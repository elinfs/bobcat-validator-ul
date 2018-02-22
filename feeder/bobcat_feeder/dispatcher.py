import asyncio
import gettext
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from .configuration import Configuration
from .mqtt_device import MQTTDevice
from .base_device import BaseDevice
from .data_packet import DataPacket
from .gps_device import GpsDevice
from .service import Service

class Dispatcher:

    def __init__(self, config: Configuration, loop: asyncio.AbstractEventLoop) -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.service = Service(config.service)
        self.loop = loop        
        self.channels = {}  # type: Dict[str, List]
        self.devices = {}  # type: Dict[str, Any]
        self.service.register_channels(self)        

    def add_device(self, dev: str, config: Dict) -> None:
        """Initialize and add device"""
        if dev == 'gps':
            self.devices[dev] = GpsDevice(config, self)
        elif dev == 'mqtt':
            self.devices[dev] = MQTTDevice(config, self)
        else:
            self.logger.error("Unknown input device configuration: {}".format(dev))

    def register_channel_function(self, channel: str, func: Callable) -> None:
        """Register channel function"""
        funcs = self.channels.get(channel)
        if funcs is None:
            funcs = []
            self.channels[channel] = funcs
        funcs.append(func)
        self.logger.debug("Registered channel %s, function %s", channel, func)

    def do_output(self, route: Optional[Union[str, List[str]]], data: DataPacket) -> None:
        """Send data to route channels, if no route send to data output channels"""
        if route:
            if isinstance(route, str):
                next_channels = [route]
            else:
                next_channels = route
        else:
            next_channels = data.outputs
        if next_channels:
            for channel in next_channels:
                funcs = self.channels.get(channel)
                if funcs:
                    for channel_func in funcs:
                        try:
                            task = channel_func(data, self)
                            if task:
                                self.loop.create_task(task)
                        except Exception as e:
                            self.logger.error("Output channel %s got an exception", channel, exc_info=e)
                else:
                    self.logger.error("Output channel missing: %s", channel)
        else:
            self.logger.error("No output available for %s", data)

    def run(self) -> None:
        """Run all device tasks and data gathering tasks"""
        self.loop.run_until_complete(asyncio.gather(*[dev.run() for dev in self.devices.values()]))