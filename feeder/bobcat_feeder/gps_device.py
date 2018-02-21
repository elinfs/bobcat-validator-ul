from typing import Dict, List, Optional, Tuple
from types import CoroutineType, FunctionType
import socket
import aiohttp
import functools
import datetime
import json
import pynmea2
import importlib

from . import dispatcher
from .base_device import BaseDevice
from .data_packet import DataPacket

DEFAULT_DRIVER = "bobcat_feeder.gps.router:Listner"

class GpsDevice(BaseDevice):
    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:
        super().__init__(self, config, dispatcher)
        self.dispatcher = dispatcher
        self.loop = dispatcher.loop
        self.done = False        
        self.outputs = config["output"]
        self.driver = config.get('driver', DEFAULT_DRIVER)
        (gps_module_str, gps_class_str) = self.driver.split(':')
        self.logger.info("Using gps driver module={} class={}".format(gps_module_str, gps_class_str))
        gps_class = getattr(importlib.import_module(gps_module_str),
                                gps_class_str)
        self.gps = gps_class(config.get('driver_config'), self)        
        self.period = config["period"]
    async def run(self) -> None:        
        self.logger.debug("Listen to gps")
        while not self.done:
            try:
                self.gps.connect()
                last_msg = ""
                while not self.done:                    
                    pos = self.gps.getPos()
                    if pos is not last_msg:
                        last_msg = pos
                        res = DataPacket.create_data_packet(pos, 'nmea_string')
                        self.dispatcher.do_output(self.outputs, res)                        
                        await asyncio.sleep(self.period)
            except Exception as ce:
                self.logger.error("Gps device exception", exc_info=ce)
