from typing import Dict, List, Optional, Tuple
from types import CoroutineType, FunctionType
import socket
import aiohttp
import asyncio
import functools
import datetime
import json
import pynmea2
import importlib

from . import dispatcher
from .base_service import BaseService
from .data_packet import DataPacket

DEFAULT_DRIVER = "bobcat_feeder.gps.router:Listner"

class GpsService(BaseService):
    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:                
        super().__init__(config, dispatcher)        
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
        self.logger.debug(self.__class__.__name__ + " init done.")

    async def run(self) -> None:        
        self.logger.debug("Listen to gps")
        await asyncio.sleep(self.period)         
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
            except OSError as ose:
                self.logger.error("Gps device os error", exc_info=ose)                
            except Exception as ce:
                self.logger.error("Gps device exception", exc_info=ce)
            self.gps.disconnect()
            await asyncio.sleep(self.period)            