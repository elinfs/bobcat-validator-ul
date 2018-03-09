import logging
import socket
import aiohttp
import datetime
import json
import pynmea2
from typing import Dict, List, Optional

class Listner:
    def __init__(self, config: Dict, service: 'GpsDevice') -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.service = service
        self.config = config        
        self.serversocket = None

    async def connect(self) -> None:  
        if self.serversocket is None:     
            self.logger.debug("Gps server: " + self.config["server"] + " port: " + str(self.config["port"]))             
            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serversocket.bind((self.config["server"], self.config["port"]))
            self.serversocket.listen(5) # become a server socket, maximum 5 connections
        else:
            self.logger.debug("Gps connection excists")

    def disconnect(self) -> None:
        self.logger.debug("Gps connection closed!")
        self.serversocket.close()
        self.serversocket = None

    def getPos(self) -> str:
        self.logger.debug("Gps pos requested!")
        connection, address = self.serversocket.accept()        
        self.logger.debug(connection)
        self.logger.debug(address)
        rawGpsData = connection.recv(4096)
        data = self.get_gps_data(rawGpsData)        
        connection.close()
        return data

    def get_gps_data(self, data: bytes):    
        datastring = str(data)    
        datastring = datastring[datastring.find('$GPRMC'):]
        strArr = datastring.split('\\r\\n')    
        return strArr[0]