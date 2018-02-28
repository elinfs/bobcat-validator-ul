import asyncio
import pynmea2
import logging
import json
import math

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from . import dispatcher
from .base_service import BaseService
from .data_packet import DataPacket

class GeoPoint:
    self.long
    self.lat
    def __init__(self, lat: float, long: float):
        self.long = math.radians(long)
        self.lat = math.radians(lat)

class StopService(BaseService):

    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:
        super().__init__(config, dispatcher)
        self.latestStops = []
        self.outputs = config["output"]
        self.geofenceradius = config["geofenceradius"]
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

    def isInGeofence(self, stopPoint: GeoPoint, point: GeoPoint) -> bool:  
        """earthRadius is the radius of the earth in km"""
        earthRadius = 6371
        dist = math.acos(math.sin(stopPoint.lat) * math.sin(point.lat) + math.cos(stopPoint.lat) * math.cos(point.lat) * math.cos(stopPoint.long - point.long)) * earthRadius
        return dist * 1000 < self.geofenceradius

    def findStop(self, point: GeoPoint) -> int:
        for stop in self.service.route:
            if isInGeofence(GeoPoint(stop.lat, stop.long), point, fenceRadius):
                return stop.id
        return -1
    
    def validateStop(self, point: GeoPoint) -> int:
        stop = findStop(point)
        if stop is not self.latestStops[-1] and stop is not -1:
            if len(self.latestStops) >= 3:
                self.latestStops.pop(0)
            self.latestStops.append(stop)
            
            