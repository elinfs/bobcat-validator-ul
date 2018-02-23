import asyncio
import pynmea2
import logging
import json

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from . import dispatcher
from .base_service import BaseService
from .data_packet import DataPacket

class StopService(BaseService):

    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:
        super().__init__(config, dispatcher)
        self.outputs = config["output"]
        self.service = {
            'line' : 'dummy',
            'route': []
        }
        self.logger.debug(self.__class__.__name__ + " init done.")
        if 'input' in config:
            for input_channel, input_config in config['input'].items():
                self.register_channel_function(input_channel, input_config)
        else:
            self.logger.debug('No Stops input channels')

    def channel_route(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> None:
        """Receive journey information"""
        if data.format == 'json':
            self.service = data.data
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))
        

    def channel_geofence(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> None:
        """Receive journey information"""
        if self.service['line'] == "dummy":
            dispatcher.do_output(self.outputs, DataPacket.create_data_packet({ 'GIDHpl': 'dummy_stop' }, 'json'))
            return
        if data.format == 'nmea_string':
            nmeastring = pynmea2.parse(data.data)             
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))        

    async def run(self):
        while not self.done:
            await asyncio.sleep(20)
            self.logger.debug("Im alive")


