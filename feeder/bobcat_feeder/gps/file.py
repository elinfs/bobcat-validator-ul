import logging
import datetime
import json
from typing import Any, Dict, List, Optional, Tuple

from typing import Dict, List, Optional

class Listner:
    def __init__(self, config: Dict, service: 'GpsDevice') -> None:
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.service = service
        self.config = config
        self.route = []            

    def connect(self) -> None:          
        with open(self.config["file"], "rt") as file:
            route = json.load(file)
            lastPoint = None
            for point in route["path"]:
                

    def disconnect(self) -> None:        

    def getPos(self) -> str:
        self.logger.debug("Gps pos requested!")        
        return data
