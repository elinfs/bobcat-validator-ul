import asyncio
import pynmea2
import logging
import json
import math

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from . import dispatcher
from .base_service import BaseService
from .data_packet import DataPacket

from pprint import pprint

DUMMYSTOP = { 'GIDHpl': 'dummy_stop' }

class GeoPoint:    
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
            self.service = json.loads(data.as_str())
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))
        

    def channel_geofence(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> None:
        """Receive journey information"""
        if self.service['line'] == "dummy":
            self.logger.debug('Geofence disabled due to unknown service')
            dispatcher.do_output(self.outputs, DataPacket.create_data_packet(DUMMYSTOP, 'json'))
            return
        if data.format == 'nmea_string':
            nmea = pynmea2.parse(data.data)             
        else:
            raise RuntimeError("Service: Unknown input format: {}".format(data.format))        
        currentStop = self.findStop(GeoPoint(nmea.latitude, nmea.longitude))
        if currentStop is not None:
            self.logger.debug('Geofence updated stops')
            dispatcher.do_output('mqtt_last_stop', DataPacket.create_data_packet({ ' GIDHpl': currentStop}, 'json'))
            dispatcher.do_output('mqtt_next_stop', DataPacket.create_data_packet(self.getNextStop(currentStop), 'json'))

    async def run(self):
        while not self.done:
            await asyncio.sleep(20)
            

    def isInGeofence(self, stopPoint: GeoPoint, point: GeoPoint) -> bool:  
        """earthRadius is the radius of the earth in km"""
        earthRadius = 6371
        dist = math.acos(math.sin(stopPoint.lat) * math.sin(point.lat) + math.cos(stopPoint.lat) * math.cos(point.lat) * math.cos(stopPoint.long - point.long)) * earthRadius
        print(str(dist * 1000))              
        return dist * 1000 < self.geofenceradius

    def findStop(self, point: GeoPoint) -> str:
        print('----------------------------------------------------------')
        for stop in self.service['route']:   
            print(" ")
            print(stop['name'])         
            if self.isInGeofence(GeoPoint(stop['coordinate']['latitude'], stop['coordinate']['longitude']), point):
                print('ankom: ' + stop['id'])
                return stop['id']
        return None
    
    def validateStop(self, point: GeoPoint) -> int:
        stop = findStop(point)
        if stop is not self.latestStops[-1] and stop is not None:
            if len(self.latestStops) >= 3:
                self.latestStops.pop(0)
            self.latestStops.append(stop)
    
    def getNextStop(self, lastStop: str) -> Dict:
        for stop in [x for x in self.service['route'] if str(x['id']) == lastStop]:
            return { ' GIDHpl': stop['id']}
        return DUMMYSTOP


            
            