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
            if is_service_updated(data.as_str()) not True:
                return
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))
        output_format = self.config['input']['service']['format']        
        if output_format == "json":
            service = json.loads(self.service)  
        else:
            raise RuntimeError("Journey input: Unknown output format: {}".format(output_format))
        try:
            self.logger.debug("Got service: %s", service)
            
            if service is not self.service:
                dispatcher.do_output(self.outputs, DataPacket.create_data_packet(service, output_format))
        except KeyError as ke:
            self.logger.error("Missing service data for %s", journey, exc_info=ke)

    def is_service_updated(self, service: str) -> bool:
        if self.service['line'] is not service:        
            self.service['line'] = service
            res = yield from aiohttp.request('get', self.config["route_url"] + service)
            data = yield from res.json()
            service['route'] = data['pointsOnRoute']
            self.logger.info("Got route for service: " + service + " | " + data['description'])
            return True
        return False    

    async def run(self):        
        while not self.done:            
            await asyncio.sleep(self.config['period'])
            self.dispatcher.do_output('mqtt_journey', DataPacket.create_data_packet(self.service, 'json'))
            