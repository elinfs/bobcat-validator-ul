import logging
import datetime
import pynmea2
import aiohttp
from typing import Any, Dict, List, Optional, Tuple

from typing import Dict, List, Optional

STEPS = 10.0

class Listner:
    def __init__(self, config: Dict, service: 'GpsDevice') -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.service = service
        self.config = config
        self.route = []            
        self.data = []
        self.pos = 0

    async def connect(self) -> None:          
        json = {} 
        async with aiohttp.ClientSession() as session:
            json = await self.fetch(session, self.config['file'])
        self.data = self.generateList(json['path'])

    def disconnect(self) -> None:        
        self.logger.debug('gps disconnect was called')

    def getPos(self) -> str:        
        self.logger.debug("Gps pos requested!")        
        latitude = self.data[self.pos]['latitude']
        longitude = self.data[self.pos]['longitude']        
        self.pos += 1
        nmeasstring = self.createNmeaString(latitude, longitude)
        self.logger.debug('latitude: ' + str(latitude) + ' | longitude: ' + str(longitude))
        self.logger.debug("Nmeastring from file: " + nmeasstring + " | " + str(self.pos) )
        return nmeasstring

    def generateList(self, data):
        response = []
        for currentPos, nextPos in zip(data[:-1],data[1:]):
            try:
                response.append(currentPos)            
                latitudeStep = (nextPos['latitude'] - currentPos['latitude']) / STEPS            
                longitudeStep = (nextPos['longitude'] - currentPos['longitude']) / STEPS            
                for x in range(int(STEPS)):  
                    pos = {'latitude': currentPos['latitude'] + (latitudeStep * x), 'longitude': currentPos['longitude'] + (longitudeStep * x)}                           
                    response.append(pos)
            except IndexError as e:
                self.logger.debug("Array has ended")
            except Exception as e:
                self.logger.error(e)
        return response
    
    async def fetch(self, session, url):    
        async with session.get(url) as response:
         return await response.json()

    def createNmeaString(self, latitude: float, longitude: float) -> str:        
        lat, lat_dir = self.decdeg2dms(latitude, 'N', 'S')
        lon, lon_dir = self.decdeg2dms(longitude, 'E', 'W')
        posdata = {'lat': lat, 'lat_dir': lat_dir, 'lon': lon, 'lon_dir': lon_dir}
        dt = datetime.datetime.utcnow()
        posdata['timestamp'] = dt.time().strftime("%H%M%S")
        posdata['datestamp'] = dt.date().strftime("%y%m%d")
        posdata['status'] = 'A'
        pos = []
        for field in pynmea2.RMC.fields:
            pos.append(posdata.get(field[1],""))
        return str(pynmea2.RMC('GP', 'RMC', pos))

    def decdeg2dms(self, dd, dirpos, dirneg):
        if dd >= 0:
            dir = dirpos
        else:
            dir = dirneg
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        if dirpos == 'N':
            return "{:02.0f}{:02.0f}.{:02.0f}".format(degrees, minutes, seconds), dir
        else:
            return "{:03.0f}{:02.0f}.{:02.0f}".format(degrees, minutes, seconds), dir