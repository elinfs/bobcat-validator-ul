from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from datetime import datetime, timedelta, timezone
import json
import logging
import asyncio
import aiohttp
from .data_packet import DataPacket
from .base_service import BaseService
from . import dispatcher

class JourneyService(BaseService):
    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:                
        super().__init__(config, dispatcher)
        self.config = config
        self.dispatcher = dispatcher    
        self.service_updated = True       
        self.outputs = config["output"]
        self.service = {
            'line' : 'dummy',
            'route': []
        }
        if 'input' in config:
            for input_channel, input_config in config['input'].items():
                self.register_channel_function(input_channel, input_config)
        else:
            self.logger.debug('No MQTT output channels')        
        self.logger.debug(self.__class__.__name__ + " init done.")
        
    def channel_service(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> None:
        """Receive journey information"""        
        if data.format == 'json':            
            service = json.loads(data.as_str())         
            self.logger.debug('channel_service called: ' + data.as_str())
            if self.service["line"] != service["line"]:
                self.service = service
                self.service_updated = True
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))
        
    async def get_service(self):              
        if self.service_updated is True and self.service['line'] != 'dummy':   
            self.service_updated = False                 
            async with aiohttp.ClientSession() as session:
                url = self.config["route_url"] + self.service['line'] 
                self.logger.debug("Service url: " + url)
                async with session.get(url) as response:            
                    data = await response.json()
            self.service['route'] = data['pointsOnRoute']
            self.logger.info("Got route for service: " + self.service['line'] + " | " + data['description'])     
            output_format = self.config['input']['service']['format']        
            if output_format == "json":
                service = json.dumps(self.service).encode()
            else:
                raise RuntimeError("Journey input: Unknown output format: {}".format(output_format))
            try:
                self.logger.debug("Got service: %s", service)                            
                self.dispatcher.do_output(self.outputs, DataPacket.create_data_packet(service, output_format))
            except KeyError as ke:
                self.logger.error("Missing service data for %s", journey, exc_info=ke)               
        else:
            self.dispatcher.do_output('mqtt_journey', DataPacket.create_data_packet(self.service, 'json'))

    async def run(self):        
        while not self.done:            
            await self.get_service()            
            await asyncio.sleep(self.config['period'])