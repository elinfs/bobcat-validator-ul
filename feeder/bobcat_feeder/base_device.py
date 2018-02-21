from typing import Awaitable, Dict, List, Optional
from types import FunctionType
import functools
import logging

from .data_packet import DataPacket
from . import dispatcher

class BaseDevice:

    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.config = config
        self.dispatcher = dispatcher
        self.done = False
        self.ready = False
        self.device_timeout = None
        self.loop = dispatcher.loop

    def get_channel_functions(self, channel: str) -> List[FunctionType]:
        """Get functions to call when we have data"""
        return self.dispatcher.channels[channel]

    def register_channel_function(self, channel: str, config: Dict) -> bool:
        """Register function to call with output data"""
        func_name = "channel_" + channel
        try:
            func = getattr(self, func_name)
            if callable(func):
                self.dispatcher.register_channel_function(channel, functools.partial(func, config=config))  # type: ignore
                return True
            else:
                self.logger.error("Output channel function not callable: {}".format(func_name))
        except AttributeError:
            print(dir(self))
            self.logger.error("Output channel function missing: {}".format(func_name))
        return False

    def call_channel(self, channel_func: FunctionType, packet: DataPacket) -> Optional[Awaitable]:
        """Call channel function passing data packet"""
        return channel_func(packet, self.dispatcher)

    def run(self):
        """Device task run method, should be overridden"""
        raise RuntimeError("ValidatorDevice run method missing")