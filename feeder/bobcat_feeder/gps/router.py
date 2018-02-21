import logging
import socket
import aiohttp
import datetime
import json
import pynmea2
from typing import Dict, List, Optional

class Listner:
    def __init__(self, config: Dict, device: 'GpsDevice') -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.device = device
        self.config = config
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:        
        self.serversocket.bind((config.server, config.port))
        self.serversocket.listen(5) # become a server socket, maximum 5 connections

    def getPos(self) -> str:
        connection, address = self.serversocket.accept()        
        rawGpsData = connection.recv(4096)
        data = get_gps_data(rawGpsData)        
        connection.close()
        return data

    def get_gps_data(data: bytes):    
    datastring = str(data)    
    datastring = datastring[datastring.find('$GPRMC'):]
    strArr = datastring.split('\\r\\n')    
    return strArr[0]